from faker import Faker

from apexdevkit.security import Hmac


def test_hmac(faker: Faker) -> None:
    message = faker.sentence()

    key_0 = faker.word()
    key_1 = faker.word()
    key_2 = faker.word()

    assert Hmac(key_0)(message) == Hmac(key_0)(message)
    assert Hmac(key_1)(message) != Hmac(key_2)(message)
