from typing import Tuple
import os
import hashlib
import hmac
import codecs
class Loguear:
    def hash_new_password(password: str) -> Tuple[bytes, bytes]:
        """
        Hash the provided password with a randomly-generated salt and return the
        salt and hash to store in the database.
        """
        salt = os.urandom(16)
        pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return salt, pw_hash

    def is_correct_password(salt: bytes, pw_hash: bytes, password: str) -> bool:
        """
        Given a previously-stored salt and hash, and a password provided by a user
        trying to log in, check whether the password is correct.
        """
        return hmac.compare_digest(
            pw_hash,
            hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        )

# Example usage:
salt, pw_hash = Loguear.hash_new_password('54321')

print (pw_hash)
hexify = codecs.getencoder('hex')
m = hexify(pw_hash)[0]
print(m.decode("utf8"))

print( Loguear.is_correct_password(salt, pw_hash, 'correct horse battery staple'))
assert not Loguear.is_correct_password(salt, pw_hash, 'Tr0ub4dor&3')
assert not Loguear.is_correct_password(salt, pw_hash, 'rosebud')