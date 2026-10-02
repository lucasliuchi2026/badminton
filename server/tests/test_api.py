from conftest import auth, client, login


def _reset_card(uid, val=0):
    from app.db import SessionLocal
    from app.models import User
    db = SessionLocal()
    u = db.get(User, uid)
    u.card_balance = val
    db.commit()
    db.close()


def test_health():
    assert client.get("/api/health").json()["ok"] is True


def test_first_user_is_owner_second_is_member():
    owner = login("boss1", "张三")
    assert owner["user"]["role"] == "owner"
    member = login("p1", "李四", "M")
    assert member["user"]["role"] == "member"
    girl = login("p2", "王五", "F")
    assert girl["user"]["role"] == "member"


def test_activity_crud_and_permissions():
    owner = login("boss1")
    member = login("p1")
    act = {
        "name": "周六晚双打局", "venue": "奥体中心 3-5号场", "date": "2026-10-04",
        "time_start": "19:00", "time_end": "21:00", "type": "paid",
        "cost_m": 30, "cost_f": 20, "cap_m": 2, "cap_f": 2,
    }
    # 普通成员不能建活动
    assert client.post("/api/activities", json=act, headers=auth(member["token"])).status_code == 403
    r = client.post("/api/activities", json=act, headers=auth(owner["token"]))
    assert r.status_code == 200, r.text
    aid = r.json()["id"]
    # 广场列表应包含该活动
    lst = client.get("/api/activities?scope=active", headers=auth(member["token"])).json()
    assert any(x["id"] == aid for x in lst)
    # 改状态（仅群主）
    assert client.post(f"/api/activities/{aid}/status", json={"status": "ongoing"},
                       headers=auth(member["token"])).status_code == 403
    assert client.post(f"/api/activities/{aid}/status", json={"status": "upcoming"},
                       headers=auth(owner["token"])).status_code == 200


def test_signup_deduct_refund_and_gating():
    owner, m = login("boss1"), login("p1")
    uid = m["user"]["id"]
    act = client.post("/api/activities", json={
        "name": "积分测试局", "venue": "T馆", "date": "2026-10-05",
        "time_start": "19:00", "time_end": "21:00", "type": "paid",
        "cost_m": 30, "cost_f": 20, "cap_m": 1, "cap_f": 0,
    }, headers=auth(owner["token"])).json()
    aid = act["id"]

    _reset_card(uid, 10)
    # 余额不足 -> 400 且不落报名
    r = client.post(f"/api/activities/{aid}/signup", json={"gender": "M", "slots": 1}, headers=auth(m["token"]))
    assert r.status_code == 400 and "点卡余额不足" in r.json()["detail"]
    assert client.get(f"/api/activities/{aid}", headers=auth(m["token"])).json()["signed_m"] == 0

    # 群主记分后报名成功，按性别单价扣 30
    client.post("/api/cards/adjust", json={"user_id": uid, "delta": 100, "memo": "记分"}, headers=auth(owner["token"]))
    r = client.post(f"/api/activities/{aid}/signup", json={"gender": "M", "slots": 1}, headers=auth(m["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["activity"]["signed_m"] == 1
    mine = client.get("/api/cards/mine", headers=auth(m["token"])).json()
    assert mine["card_balance"] == 80  # 10 + 100记分 - 30报名
    assert mine["logs"][0]["biz"] == "signup"

    # 男名额已满（cap_m=1）
    r = client.post(f"/api/activities/{aid}/signup", json={"gender": "M", "slots": 1}, headers=auth(m["token"]))
    assert r.status_code == 400 and "名额不足" in r.json()["detail"]
    # 女名额为 0
    r = client.post(f"/api/activities/{aid}/signup", json={"gender": "F", "slots": 1}, headers=auth(m["token"]))
    assert r.status_code == 400

    # 取消：他人不可代取消；本人可取消且退款；名额释放
    reg_id = r2 = None
    detail = client.get(f"/api/activities/{aid}", headers=auth(m["token"])).json()
    reg_id = detail["registrations_m"][0]["id"]
    other = login("p3", "赵六")
    assert client.post(f"/api/activities/registrations/{reg_id}/cancel", headers=auth(other["token"])).status_code == 403
    assert client.post(f"/api/activities/registrations/{reg_id}/cancel", headers=auth(m["token"])).status_code == 200
    mine = client.get("/api/cards/mine", headers=auth(m["token"])).json()
    assert mine["card_balance"] == 110 and mine["logs"][0]["biz"] == "refund"


def test_proxy_signup_names_count_validated():
    owner, m = login("boss1"), login("p1")
    aid = client.post("/api/activities", json={
        "name": "代报测试局", "venue": "T馆2", "date": "2026-10-06",
        "time_start": "19:00", "time_end": "21:00", "type": "free", "cap_m": 5, "cap_f": 5,
    }, headers=auth(owner["token"])).json()["id"]
    # slots 与 names 不一致 -> 400
    r = client.post(f"/api/activities/{aid}/signup",
                    json={"gender": "M", "slots": 3, "names": ["小明"]}, headers=auth(m["token"]))
    assert r.status_code == 400
    r = client.post(f"/api/activities/{aid}/signup",
                    json={"gender": "M", "slots": 3, "names": ["小明", "小刚"]}, headers=auth(m["token"]))
    assert r.status_code == 200
    detail = client.get(f"/api/activities/{aid}", headers=auth(m["token"])).json()
    assert detail["signed_m"] == 3
    names = {x["member_name"] for x in detail["registrations_m"]}
    assert names == {"李四", "小明", "小刚"}


def test_free_activity_no_deduction():
    owner, m = login("boss1"), login("p1")
    bal0 = client.get("/api/cards/mine", headers=auth(m["token"])).json()["card_balance"]
    aid = client.post("/api/activities", json={
        "name": "免费局测试", "venue": "T馆3", "date": "2026-10-07",
        "time_start": "19:00", "time_end": "21:00", "type": "free", "cap_m": 2, "cap_f": 2,
    }, headers=auth(owner["token"])).json()["id"]
    r = client.post(f"/api/activities/{aid}/signup", json={"gender": "F", "slots": 1}, headers=auth(m["token"]))
    assert r.status_code == 200
    assert client.get("/api/cards/mine", headers=auth(m["token"])).json()["card_balance"] == bal0


def test_match_and_standings_flow():
    owner, a, b = login("boss1"), login("p1"), login("p2")
    # 成员不能录分
    body = {"player_a_id": a["user"]["id"], "player_b_id": b["user"]["id"],
            "score_a": 2, "score_b": 1, "detail": "21-15,18-21,21-13", "played_at": "2026-10-01"}
    assert client.post("/api/league/matches", json=body, headers=auth(a["token"])).status_code == 403
    # 平局拒绝
    bad = dict(body, score_b=2)
    assert client.post("/api/league/matches", json=bad, headers=auth(owner["token"])).status_code == 400
    assert client.post("/api/league/matches", json=body, headers=auth(owner["token"])).status_code == 200
    board = client.get("/api/league/standings", headers=auth(a["token"])).json()
    ra = next(x for x in board if x["user_id"] == a["user"]["id"])
    rb = next(x for x in board if x["user_id"] == b["user"]["id"])
    assert (ra["points"], ra["wins"]) == (25, 1) or ra["points"] >= 25
    assert rb["points"] >= 5
    assert board[0]["points"] >= board[-1]["points"]
    assert len(client.get("/api/league/matches", headers=auth(a["token"])).json()) >= 1


def test_card_privacy_and_owner_view():
    owner, m = login("boss1"), login("p1")
    other = login("p4", "孙九")
    # 成员不能看他人流水
    assert client.get(f"/api/cards/logs?user_id={other['user']['id']}", headers=auth(m["token"])).status_code == 403
    # 群主可看全员
    assert client.get(f"/api/cards/logs?user_id={other['user']['id']}", headers=auth(owner["token"])).status_code == 200
    users = client.get("/api/cards/users", headers=auth(owner["token"])).json()
    assert any(u["card_balance"] >= 0 for u in users)
    assert client.get("/api/cards/users", headers=auth(m["token"])).status_code == 403


def test_review_placeholder_and_group_config():
    owner, m = login("boss1"), login("p1")
    cfg = client.get("/api/group", headers=auth(m["token"])).json()
    assert cfg["slogan"]
    # 成员不能改群配置
    assert client.put("/api/group", json={"slogan": "新口号"}, headers=auth(m["token"])).status_code == 403
    assert client.put("/api/group", json={"slogan": "新口号"}, headers=auth(owner["token"])).json()["slogan"] == "新口号"
    aid = client.post("/api/activities", json={
        "name": "回顾测试局", "venue": "T馆9", "date": "2026-10-09",
        "time_start": "19:00", "time_end": "21:00", "type": "free", "cap_m": 1, "cap_f": 1,
    }, headers=auth(owner["token"])).json()["id"]
    client.post(f"/api/activities/{aid}/signup", json={"gender": "M", "slots": 1}, headers=auth(owner["token"]))
    rev = client.get(f"/api/activities/{aid}/review", headers=auth(m["token"])).json()
    assert "活动回顾" in rev["text"] and rev["engine"] == "template"
