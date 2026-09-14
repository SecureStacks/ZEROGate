from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
scenarios = client.get("/api/demo/scenarios").json()
scenario_b = [s for s in scenarios if s["id"] == "scenario-b"][0]
reqs = client.get("/api/access-requests").json()
match = [r for r in reqs if r["source_ip"] == scenario_b["network"]["source_ip"]][0]

pep_res = client.post("/api/pep/enforce", json={"access_request_id": match["id"]})
print("PEP DECISION:", pep_res.json())

pdp_res = client.post("/api/pdp/evaluate", json={"access_request_id": match["id"]})
print("PDP DECISION:", pdp_res.json())
