# Common test data
MALICIOUS_STRINGS = [
    "'; DROP TABLE users; --",
    "<script>alert('xss')</script>",
    "admin'/*",
    "1' OR '1'='1",
    "'; DELETE FROM sessions; --",
    "<img src=x onerror=alert('xss')>",
    "../../etc/passwd",
    "\x00\x01\x02",
]

INVALID_WORKOUT_NAMES = [
    "",
    "   ",
    "Test@Workout",
    "Workout$pecial",
    "Test\x00Null",
    "a" * 150,  # Too long
]

INVALID_INTENSITIES = [
    "extreme",
    "SUPER_HIGH",
    "invalid",
    "",
    None,
    123,
]

INVALID_REP_COUNTS = [
    0,
    -1,
    1001,
    "ten",
    None,
    3.14,
]