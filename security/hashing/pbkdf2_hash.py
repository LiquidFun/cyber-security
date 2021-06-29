import os
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from security.hashing.generic_hash import GenericHash
from security.utils.hash_utils import HashUtils


class Pbkdf2Hash(GenericHash):

    # https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#pbkdf2

    def __init__(self, is_test: Optional[bool] = False):
        super().__init__()

        # defaults
        self.__hash_length = 32
        self.__hash_iterations = 100000

        self.__salt_length = 16

        self.__is_test = is_test

    def get_key(self) -> bytes:

        salt = os.urandom(self.__salt_length)
        print(f'salt: {salt.hex()}')

        password_bytes = HashUtils.get_password(self.__is_test)

        key = self.__derive_key(password_bytes, salt)

        return key

    def get_key_with_existing_credentials(self) -> bytes:

        salt = HashUtils.get_salt_from_user()

        password_bytes = HashUtils.get_password_from_user()

        key = self.__derive_key(password_bytes, salt)

        return key

    def __derive_key(self, password_bytes: bytes, salt: bytes) -> bytes:
        kdf = self.__get_kdf_instance(salt)
        key = kdf.derive(password_bytes)

        kdf = self.__get_kdf_instance(salt)
        kdf.verify(password_bytes, key)

        return key

    def __get_kdf_instance(self, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.__hash_length,
            salt=salt,
            iterations=self.__hash_iterations,
        )

        return kdf