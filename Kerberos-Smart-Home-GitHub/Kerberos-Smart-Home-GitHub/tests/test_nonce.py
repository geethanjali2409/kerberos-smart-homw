import time
import uuid

from security.nonce_manager import check_freshness


timestamp = time.time()
nonce = str(uuid.uuid4())


print("Testing fresh message...")

valid, reason = check_freshness(timestamp, nonce)

print("Valid:", valid)
print("Reason:", reason)


print("\nTesting replay attack...")

valid, reason = check_freshness(timestamp, nonce)

print("Valid:", valid)
print("Reason:", reason)


print("\nTesting old message...")

old_timestamp = time.time() - 20
old_nonce = str(uuid.uuid4())

valid, reason = check_freshness(old_timestamp, old_nonce)

print("Valid:", valid)
print("Reason:", reason)