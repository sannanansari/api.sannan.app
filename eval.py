import requests

API = "http://localhost:8000";
passed = 0;
failed = 0;
results = [];

def check(test_name: str, condition: str, actual: str):
    global passed, failed;
    if condition:
        passed += 1
        results.append(f"  ✓ {test_name}")
    else:
        failed += 1
        results.append(f"  ✗ {test_name} → got: {actual}")

print("\n Running evals ... \n");

res = requests.get(f"{API}/tea-structured/darjeeling").json();

check (
    "darjeeling has name",
    len(res["name"]) > 0,
    res["name"]
)

check(
    "darjeeling origin contains India",
    "india" in res["origin"].lower(),
    res["origin"]
)
check(
    "darjeeling has flavour profile",
    len(res["flavour_profile"]) > 0,
    res["flavour_profile"]
)
check(
    "darjeeling caffeine level not empty",
    len(res["caffeine_level"]) > 0,
    res["caffeine_level"]
)
# Test 2 — Oolong classification
res = requests.get(f"{API}/tea_classifies/oolong").json()

check(
    "oolong not classified as black tea",
    "black" not in res["classifies_type"].lower(),
    res["classifies_type"]
)
check(
    "oolong origin is taiwan or china",
    any(x in res["origin_region"].lower() for x in ["taiwan", "china"]),
    res["origin_region"]
)

# Test 3 — Green tea classification
res = requests.get(f"{API}/tea_classifies/green").json()

check(
    "green tea classified correctly",
    "green" in res["classifies_type"].lower(),
    res["classifies_type"]
)

# Test 4 — Positive review
res = requests.post(f"{API}/getReviewSentiments", json={
    "review": "This tea was absolutely incredible. Smooth, earthy, and calming. Would buy again."
}).json()

check(
    "positive review detected as positive",
    res["sentiment"].lower() == "positive",
    res["sentiment"]
)
check(
    "positive review has high rating",
    any(x in res["rating"].lower() for x in ["5", "4", "high", "excellent"]),
    res["rating"]
)

# Test 5 — Negative review
res = requests.post(f"{API}/getReviewSentiments", json={
    "review": "Terrible tea. Bitter, stale, and overpriced. Never buying again."
}).json()

check(
    "negative review detected as negative",
    res["sentiment"].lower() == "negative",
    res["sentiment"]
)

# Test 6 — Tea extractor
res = requests.post(f"{API}/teaextractor", json={
    "review": "I had this amazing light golden tea from the hills of Darjeeling. Muscatel flavour with floral notes. Best without milk."
}).json()

check(
    "extractor finds darjeeling origin",
    "darjeeling" in res["origin"].lower(),
    res["origin"]
)
check(
    "extractor finds flavour profile",
    len(res["flavour_profile"]) > 0,
    res["flavour_profile"]
)
check(
    "extractor finds serving suggestion",
    len(res["best_served"]) > 0,
    res["best_served"]
)

# Test 7 — Chat endpoint
res = requests.post(f"{API}/chat", json={
    "question": "What is a virtual environment in Python?"
}).json()

check(
    "chat returns answer",
    len(res["answer"]) > 0,
    res.get("answer", "")[:50]
)
check(
    "chat answer mentions venv or virtual",
    any(x in res["answer"].lower() for x in ["venv", "virtual", "environment", "isolated"]),
    res["answer"][:80]
)

# Results
total = passed + failed
score = int((passed / total) * 100) if total > 0 else 0

print("Results:")
for r in results:
    print(r)

print(f"\n{'─' * 40}")
print(f"Score: {passed}/{total} ({score}%)")
print(f"Passed: {passed}  Failed: {failed}")
print(f"{'─' * 40}\n")

if score == 100:
    print("All evals passing. Safe to deploy.")
elif score >= 80:
    print("Most evals passing. Review failures before deploy.")
else:
    print("Too many failures. Fix before deploy.")
    
    