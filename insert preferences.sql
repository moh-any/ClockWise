INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'sofia.jensen1@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'sofia.jensen1@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'sofia.jensen1@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'sofia.jensen1@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'sofia.jensen1@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'emma.nielsen2@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'emma.nielsen2@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'emma.nielsen2@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'emma.nielsen2@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'emma.nielsen2@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'lukas.hansen3@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lukas.hansen3@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lukas.hansen3@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lukas.hansen3@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lukas.hansen3@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'oliver.pedersen4@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'oliver.pedersen4@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'oliver.pedersen4@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'oliver.pedersen4@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'oliver.pedersen4@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'amelia.andersen5@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'amelia.andersen5@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'amelia.andersen5@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'amelia.andersen5@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'amelia.andersen5@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'mason.christensen6@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'mason.christensen6@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'mason.christensen6@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'mason.christensen6@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'mason.christensen6@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'isabella.larsen7@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'isabella.larsen7@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'isabella.larsen7@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'isabella.larsen7@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'isabella.larsen7@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'evelyn.sorensen8@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'evelyn.sorensen8@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'evelyn.sorensen8@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'evelyn.sorensen8@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'evelyn.sorensen8@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'abigail.rasmussen9@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'abigail.rasmussen9@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'abigail.rasmussen9@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'abigail.rasmussen9@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'abigail.rasmussen9@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'ava.olsen10@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ava.olsen10@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ava.olsen10@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ava.olsen10@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ava.olsen10@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'lucas.thomsen11@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lucas.thomsen11@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lucas.thomsen11@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lucas.thomsen11@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lucas.thomsen11@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'olivia.kristensen12@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'olivia.kristensen12@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'olivia.kristensen12@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'olivia.kristensen12@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'olivia.kristensen12@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'noah.jorgensen13@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'noah.jorgensen13@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'noah.jorgensen13@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'noah.jorgensen13@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'noah.jorgensen13@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'mia.madsen14@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'mia.madsen14@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'mia.madsen14@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'mia.madsen14@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'mia.madsen14@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'harper.mortensen15@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'harper.mortensen15@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'harper.mortensen15@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'harper.mortensen15@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'harper.mortensen15@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'james.frederiksen16@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'james.frederiksen16@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'james.frederiksen16@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'james.frederiksen16@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'james.frederiksen16@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'charlotte.berg17@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'charlotte.berg17@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'charlotte.berg17@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'charlotte.berg17@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'charlotte.berg17@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'liam.lund18@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'liam.lund18@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'liam.lund18@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'liam.lund18@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'liam.lund18@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'ella.holm19@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ella.holm19@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ella.holm19@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ella.holm19@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ella.holm19@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'benjamin.moller20@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'benjamin.moller20@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'benjamin.moller20@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'benjamin.moller20@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'benjamin.moller20@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'aria.dahl21@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'aria.dahl21@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'aria.dahl21@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'aria.dahl21@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'aria.dahl21@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'ethan.eriksen22@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ethan.eriksen22@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ethan.eriksen22@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ethan.eriksen22@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'ethan.eriksen22@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'lily.bakke23@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lily.bakke23@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lily.bakke23@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lily.bakke23@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'lily.bakke23@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'alexander.strand24@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'alexander.strand24@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'alexander.strand24@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'alexander.strand24@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'alexander.strand24@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'chloe.aas25@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'chloe.aas25@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'chloe.aas25@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'chloe.aas25@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'chloe.aas25@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'william.haugen26@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'william.haugen26@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'william.haugen26@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'william.haugen26@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'william.haugen26@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'grace.lie27@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'grace.lie27@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'grace.lie27@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'grace.lie27@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'grace.lie27@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'daniel.berge28@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'daniel.berge28@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'daniel.berge28@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'daniel.berge28@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'daniel.berge28@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'nora.vik29@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'nora.vik29@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'nora.vik29@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'nora.vik29@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'nora.vik29@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'sebastian.solberg30@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'sebastian.solberg30@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'sebastian.solberg30@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'sebastian.solberg30@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'sebastian.solberg30@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'hannah.dale31@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'hannah.dale31@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'hannah.dale31@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'hannah.dale31@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'hannah.dale31@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'leo.nygaard32@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'leo.nygaard32@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'leo.nygaard32@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'leo.nygaard32@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'leo.nygaard32@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'zoe.brun33@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'zoe.brun33@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'zoe.brun33@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'zoe.brun33@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'zoe.brun33@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'henry.hagen34@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'henry.hagen34@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'henry.hagen34@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'henry.hagen34@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'henry.hagen34@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;

INSERT INTO employees_preferences(employee_id, day, preferred_start_time, preferred_end_time, available_start_time, available_end_time)
VALUES
  ((SELECT id FROM users WHERE email = 'victoria.roed35@example.com'), 'sunday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'victoria.roed35@example.com'), 'monday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'victoria.roed35@example.com'), 'tuesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'victoria.roed35@example.com'), 'wednesday', '08:00:00', '22:00:00', '08:00:00', '22:00:00'),
((SELECT id FROM users WHERE email = 'victoria.roed35@example.com'), 'thursday', '08:00:00', '22:00:00', '08:00:00', '22:00:00')
ON CONFLICT DO NOTHING;