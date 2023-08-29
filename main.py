import random
import socket
from math import sin


def test(a: int, b: int) -> int:
    return a + b


class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def login(self):
        print("привет Successfully logged at " + self.username + "!")
        print(random.randint(1, 100))
        print(sin(321221))

user = User("Roman", "423234326")
user.login()
user.login()
user2 = User("Bonjur", "fddsfsdf")
user2.login()
