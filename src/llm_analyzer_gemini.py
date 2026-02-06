"""
LLM-Enhanced Surge Analysis using Google Gemini (FREE)
Deep analysis for high-risk surges only (risk_score > 0.7)

Free Tier: 15 requests/minute, 1500 requests/day
Perfect for surge detection with moderate volume.
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class GeminiSurgeAnalyzer:
    """
    Deep surge analysis using Google Gemini (FREE tier).
    Only call when risk_score > 0.7 to conserve quota.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini analyzer.
        
        Args:
            api_key: Google API key. If None, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY env var or pass api_key. "
                "Get free key at: https://makersuite.google.com/app/apikey"
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Try multiple model names in order of preference
        # Model names that work as of 2026
        self.model_names_to_try = [
            'gemini-pro',                    # Most reliable, widely available
            'gemini-2.5-flash',              # Newer, faster
            'models/gemini-pro',             # With models/ prefix
            'gemini-1.5-pro',                # Pro version
        ]
        
        # Start with the first model (will fallback during use if needed)
        self.current_model_index = 0
        self.model = genai.GenerativeModel(self.model_names_to_try[0])
        
        # Track usage for monitoring
        self.call_count = 0
        self.total_tokens = 0
        
    def analyze_surge_context(self,
                              venue_name: str,
                              surge_metrics: 'SurgeEvent',
                              social_posts: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Deep analysis of surge using Google Gemini FREE API.
        
        Only called when:
        - risk_score > 0.7 (high-risk surges)
        - Within daily quota (1500 requests/day)
        
        Args:
            venue_name: Name of the venue
            surge_metrics: SurgeEvent object with full context
            social_posts: Optional list of recent social media posts
        
        Returns:
            {
                'root_cause_detailed': str,
                'viral_potential': float (0-1),
                'urgency_level': float (0-1),
                'recommended_response': str,
                'estimated_duration_hours': int,
                'confidence': float (0-1),
                'model_used': 'gemini-1.5-flash'
            }
        """
        if social_posts is None:
            social_posts = []
        
        # Build context for LLM
        context = self._build_context(venue_name, surge_metrics, social_posts)
        
        # Create prompt
        prompt = self._build_prompt(context)
        
        try:
            # Call Gemini API (FREE)
            self.call_count += 1
            
            # Try current model, fallback to others if needed
            response = None
            last_error = None
            
            for attempt, model_name in enumerate(self.model_names_to_try):
                try:
                    if attempt > 0:
                        print(f"   Trying alternative model: {model_name}")
                        self.model = genai.GenerativeModel(model_name)
                    
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                            max_output_tokens=100000,  # Increased from 500 to ensure complete responses
                        ),
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        }
                    )
                    
                    # Check if response was blocked or incomplete
                    if not response or not response.text:
                        raise Exception("Empty response from model")
                    
                    if len(response.text) < 50:
                        raise Exception(f"Response too short ({len(response.text)} chars) - likely incomplete: {response.text}")
                    
                    # Success! Remember this model for next time
                    if attempt > 0:
                        self.current_model_index = attempt
                        print(f"   ✅ Using {model_name} for future calls")
                    
                    break
                    
                except Exception as e:
                    last_error = e
                    if "404" in str(e) or "not found" in str(e).lower():
                        # Model not found, try next one
                        continue
                    else:
                        # Different error, don't retry
                        raise
            
            if response is None:
                raise Exception(f"All models failed. Last error: {last_error}")
            
            # Track token usage (informational, not billed)
            if hasattr(response, 'usage_metadata'):
                self.total_tokens += response.usage_metadata.total_token_count
            
            # Parse response
            result = self._parse_response(response.text)
            result['model_used'] = self.model._model_name if hasattr(self.model, '_model_name') else 'gemini'
            result['call_number'] = self.call_count
            
            return result
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            # Return fallback analysis
            return self._fallback_analysis(surge_metrics)
    
    def _build_context(self, venue_name: str, surge: 'SurgeEvent', posts: List[str]) -> str:
        """Build context string for LLM."""
        social_signals = surge.metrics_window[-1].social_signals if surge.metrics_window else {}
        
        context = f"""Venue: {venue_name}
Current surge detected:
- Average ratio: {surge.avg_ratio:.2f}x normal demand
- Severity: {surge.severity}
- Trend: {surge.trend}
- Risk score: {surge.risk_score:.2f}
- Social signals: {json.dumps(social_signals, indent=2)}

Recent social media activity:"""
        
        if posts:
            for i, post in enumerate(posts[:10], 1):
                context += f"\n{i}. {post[:200]}"  # Limit post length
        else:
            context += "\n(No social media posts available)"
        
        return context
    
    def _build_prompt(self, context: str) -> str:
        """Build prompt for Gemini."""
        return f"""{context}

Analyze this demand surge and provide:

1. **Root Cause** (detailed): What is driving this surge? (influencer post, viral trend, event, news, etc.)
2. **Viral Potential** (0-1): Likelihood this will continue spreading virally
3. **Urgency Level** (0-1): How soon manager must act (0=can wait, 1=immediate action needed)
4. **Recommended Response**: Specific, actionable steps for the manager
5. **Estimated Duration**: How many hours will this surge last?
6. **Confidence** (0-1): How confident are you in this analysis?

CRITICAL: Respond with valid JSON only. Each string value MUST be on a single line - no line breaks within strings.

{{
    "root_cause_detailed": "Brief explanation in 1-2 sentences on a single line",
    "viral_potential": 0.0,
    "urgency_level": 0.0,
    "recommended_response": "Concise action steps on a single line",
    "estimated_duration_hours": 0,
    "confidence": 0.0
}}"""
    
    def _parse_response(self, response_text: str) -> Dict[str, any]:
        """Parse JSON response from Gemini."""
        try:
            # Clean up response (remove markdown if present)
            cleaned = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned.startswith('```'):
                parts = cleaned.split('```')
                if len(parts) >= 2:
                    cleaned = parts[1]
                    if cleaned.startswith('json'):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
            
            # Remove any trailing markdown
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].strip()
            
            # Fix common JSON issues: escape literal newlines within string values
            # This fixes the "Unterminated string" error when Gemini includes newlines
            import re
            
            # Strategy: Replace literal newlines in string values
            # We need to be careful to only replace newlines INSIDE quoted strings
            
            # First, try a simple approach: find all string values and fix them
            def fix_json_strings(text):
                """Fix newlines within JSON string values."""
                result = []
                in_string = False
                escape_next = False
                
                for i, char in enumerate(text):
                    if escape_next:
                        result.append(char)
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        result.append(char)
                        escape_next = True
                        continue
                    
                    if char == '"':
                        in_string = not in_string
                        result.append(char)
                        continue
                    
                    if in_string and char in ('\n', '\r'):
                        # Replace literal newline with escaped version
                        result.append('\\n' if char == '\n' else '\\r')
                    else:
                        result.append(char)
                
                return ''.join(result)
            
            cleaned = fix_json_strings(cleaned)
            
            # Try to parse JSON
            result = json.loads(cleaned)
            
            # Validate and convert types (unescape \\n back to space for readability)
            return {
                'root_cause_detailed': str(result.get('root_cause_detailed', 'Unable to determine')).replace('\\n', ' ').replace('\n', ' ').strip(),
                'viral_potential': float(result.get('viral_potential', 0.5)),
                'urgency_level': float(result.get('urgency_level', 0.7)),
                'recommended_response': str(result.get('recommended_response', 'Follow standard protocol')).replace('\\n', ' ').replace('\n', ' ').strip(),
                'estimated_duration_hours': int(result.get('estimated_duration_hours', 3)),
                'confidence': float(result.get('confidence', 0.5))
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Failed to parse Gemini response: {e}")
            print(f"\nFull raw response ({len(response_text)} chars):")
            print("-" * 70)
            print(response_text)
            print("-" * 70)
            print("\nAttempting relaxed parsing...")
            
            # Fallback: Try to extract values using regex if JSON parsing fails
            try:
                import re
                result = {}
                
                # Extract root_cause_detailed (allow any characters including newlines until the next JSON key or closing brace)
                match = re.search(r'"root_cause_detailed"\s*:\s*"(.*?)"(?:\s*,|\s*})', response_text, re.DOTALL)
                if match:
                    result['root_cause_detailed'] = match.group(1).replace('\\n', ' ').replace('\n', ' ').strip()
                
                # Extract viral_potential
                match = re.search(r'"viral_potential"\s*:\s*([0-9.]+)', response_text)
                if match:
                    result['viral_potential'] = float(match.group(1))
                
                # Extract urgency_level
                match = re.search(r'"urgency_level"\s*:\s*([0-9.]+)', response_text)
                if match:
                    result['urgency_level'] = float(match.group(1))
                
                # Extract recommended_response (allow any characters including newlines)
                match = re.search(r'"recommended_response"\s*:\s*"(.*?)"(?:\s*,|\s*})', response_text, re.DOTALL)
                if match:
                    result['recommended_response'] = match.group(1).replace('\\n', ' ').replace('\n', ' ').strip()
                
                # Extract estimated_duration_hours
                match = re.search(r'"estimated_duration_hours"\s*:\s*([0-9]+)', response_text)
                if match:
                    result['estimated_duration_hours'] = int(match.group(1))
                
                # Extract confidence
                match = re.search(r'"confidence"\s*:\s*([0-9.]+)', response_text)
                if match:
                    result['confidence'] = float(match.group(1))
                
                if result:
                    print("✅ Relaxed parsing succeeded!")
                    return {
                        'root_cause_detailed': result.get('root_cause_detailed', 'Unable to determine'),
                        'viral_potential': result.get('viral_potential', 0.5),
                        'urgency_level': result.get('urgency_level', 0.7),
                        'recommended_response': result.get('recommended_response', 'Follow standard protocol'),
                        'estimated_duration_hours': result.get('estimated_duration_hours', 3),
                        'confidence': result.get('confidence', 0.5)
                    }
            except Exception as regex_error:
                print(f"Relaxed parsing also failed: {regex_error}")
            
            # Final fallback
            return {
                'root_cause_detailed': 'Analysis parsing failed',
                'viral_potential': 0.5,
                'urgency_level': 0.7,
                'recommended_response': 'Follow standard surge protocol',
                'estimated_duration_hours': 3,
                'confidence': 0.3
            }
    
    def _fallback_analysis(self, surge: 'SurgeEvent') -> Dict[str, any]:
        """Fallback analysis when API fails."""
        return {
            'root_cause_detailed': 'LLM analysis unavailable - using numeric signals only',
            'viral_potential': 0.0,
            'urgency_level': surge.risk_score,
            'recommended_response': 'Follow standard surge response protocol',
            'estimated_duration_hours': 3,
            'confidence': 0.0,
            'model_used': 'fallback'
        }
    
    def get_usage_stats(self) -> Dict[str, any]:
        """Get usage statistics for monitoring."""
        return {
            'total_calls': self.call_count,
            'total_tokens': self.total_tokens,
            'daily_limit': 1500,
            'calls_remaining': max(0, 1500 - self.call_count),
            'cost': 0.0  # FREE!
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at midnight)."""
        self.call_count = 0
        self.total_tokens = 0


def test_gemini_analyzer():
    """
    Test Gemini analyzer with sample surge event.
    Requires GEMINI_API_KEY environment variable.
    """
    print("=" * 70)
    print("GEMINI LLM ANALYZER TEST")
    print("=" * 70)
    
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print("\n❌ GEMINI_API_KEY not set!")
        print("\n📝 To get a FREE API key:")
        print("   1. Go to: https://makersuite.google.com/app/apikey")
        print("   2. Sign in with Google account")
        print("   3. Click 'Create API Key'")
        print("   4. Set environment variable: $env:GEMINI_API_KEY='your_key_here'")
        print("\nFree tier: 15 requests/minute, 1500 requests/day")
        return
    
    try:
        # Initialize analyzer
        print("\n1. Initializing Gemini analyzer (FREE tier)...")
        analyzer = GeminiSurgeAnalyzer()
        print("   ✅ Connected to Gemini API")
        
        # Create sample surge event
        print("\n2. Creating sample surge scenario...")
        from surge_detector import SurgeEvent, SurgeMetrics
        
        metrics = [
            SurgeMetrics(
                timestamp=datetime.now(),
                actual=320,
                predicted=100,
                ratio=3.2,
                social_signals={
                    'google_trends': 85,
                    'twitter_mentions': 127,
                    'twitter_virality': 0.89,
                    'composite_signal': 0.82
                },
                excess_demand=220
            )
        ]
        
        event = SurgeEvent(
            place_id=456,
            detected_at=datetime.now(),
            severity='critical',
            risk_score=0.85,
            avg_ratio=3.2,
            trend='accelerating',
            root_cause='social_media_viral',
            metrics_window=metrics,
            recommendations=["Urgent action needed"],
            estimated_duration="4-6 hours"
        )
        
        # Simulate social media posts
        sample_posts = [
            "OMG just tried the secret burger at Downtown Spot! 🔥 Must try! #foodie",
            "This place is INSANE right now! Line out the door! Worth it though 😍",
            "TikTok brought me here and wow... best decision ever! 💯"
        ]
        
        print("   ✅ Sample surge: 3.2x demand, critical severity")
        
        # Run analysis
        print("\n3. Calling Gemini API for deep analysis...")
        print("   (This may take 2-3 seconds...)")
        
        analysis = analyzer.analyze_surge_context(
            venue_name="Downtown Spot",
            surge_metrics=event,
            social_posts=sample_posts
        )
        
        print("   ✅ Analysis complete!")
        
        # Display results
        print("\n4. Analysis Results:")
        print("-" * 70)
        print(f"Root Cause: {analysis['root_cause_detailed']}")
        print(f"Viral Potential: {analysis['viral_potential']:.0%}")
        print(f"Urgency Level: {analysis['urgency_level']:.0%}")
        print(f"Estimated Duration: {analysis['estimated_duration_hours']} hours")
        print(f"Confidence: {analysis['confidence']:.0%}")
        print(f"Model Used: {analysis.get('model_used', 'N/A')}")
        print()
        print("Recommended Response:")
        print(f"  {analysis['recommended_response']}")
        print("-" * 70)
        
        # Show usage stats
        stats = analyzer.get_usage_stats()
        print("\n5. Usage Statistics (FREE tier):")
        print(f"   Calls today: {stats['total_calls']} / {stats['daily_limit']}")
        print(f"   Remaining: {stats['calls_remaining']} calls")
        print(f"   Tokens used: {stats['total_tokens']}")
        print(f"   Cost: ${stats['cost']:.2f} (FREE!)")
        
        print("\n" + "=" * 70)
        print("✅ Test complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_gemini_analyzer()
