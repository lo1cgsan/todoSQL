INSERT INTO users (email, haslo)
VALUES
  ('adres1@wp.pl', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('adres2@wp.pl', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO zadania (id_user, zadanie, data_pub)
VALUES (1, 'test' || x'0a' || 'body', '2018-01-01 00:00:00');