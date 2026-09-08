from security.auth import create_signature, verify_signature


message = {
    "device": "door1",
    "doorOpen": True
}


# Create signature
signature = create_signature(message)

print("Original message:")
print(message)

print("\nSignature:")
print(signature)


# Verify original message
print("\nOriginal verification:")

if verify_signature(message, signature):
    print("AUTHENTICATION SUCCESS")
else:
    print("AUTHENTICATION FAILED")


# Tamper with message
tampered_message = {
    "device": "door1",
    "doorOpen": False
}


print("\nTampered message:")
print(tampered_message)

print("\nTampered verification:")

if verify_signature(tampered_message, signature):
    print("SECURITY FAILURE")
else:
    print("TAMPERING DETECTED")