import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001"


def call(path, data=None, token=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method or ("POST" if body else "GET"))
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


status, login = call("/auth/wx-login", {"code": "dev_demo_user_001"})
print("login", status, "user", login.get("user_id"), "nick", login.get("nickname"))
tok = login["token"]

status, stats = call("/profile/stats", token=tok)
print("stats", status, "level", stats["level"], "exp", stats["exp"],
      "skin", stats["skin"], stats["skin_name"], "dark", stats["skin_dark"])
print("stars", stats["total_stars"], "/", stats["max_stars"], "tokens", len(stats["skin_tokens"]))
for k in stats["skins"]:
    print("  ", k["id"].ljust(10), k["name"], k["unlock_type"],
          "unlocked=" + str(k["unlocked"]), "equipped=" + str(k["equipped"]),
          "|", k["unlock_hint"], "|", k["rarity_name"])

status, listed = call("/profile/skins", token=tok)
print("GET /profile/skins", status, len(listed))

for skin_id in ["ocean", "cyber", "aurora", "nope", "classic"]:
    status, res = call("/profile/skin", {"skin_id": skin_id}, token=tok)
    if status == 200:
        worn = [x["id"] for x in res if x["equipped"]]
        print("equip", skin_id, status, "worn ->", worn)
    else:
        print("equip", skin_id, status, res.get("detail"))
