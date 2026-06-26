import sys
sys.path.insert(0, 'src')

from engine.time_manager import TimeManager
from engine.economy_manager import EconomyManager
from business.manager import BusinessManager, MissionState
from business.marketing import MarketingManager
from business.jobs import Lead, LeadGenerator, Urgency


def setup():
    tm = TimeManager()
    em = EconomyManager(personal=50_000.0, business=5_000.0)
    bm = BusinessManager()
    mm = MarketingManager()
    bm.register(em)
    bm.pop_notifications()
    bm.buy_kit(em)
    bm.pop_notifications()
    return tm, em, bm, mm


# ── Test 1 : rate=0 → never fires ─────────────────────────────────────────
print("=== Test 1 : Budget pub 0 = aucun lead ===")
gen = LeadGenerator()
gen._cooldown = 0.0
for _ in range(10_000):
    assert gen.update(1.0, 10, rate=0.0) is None
print("PASS – 10 000 ticks a rate=0, aucun lead genere")

# ── Test 2 : accept blocked with stock=0 ──────────────────────────────────
print("\n=== Test 2 : Refus si stock epuise ===")
tm, em, bm, mm = setup()
lead = Lead(description="Porte claquee", urgency=Urgency.MEDIUM, distance=5.0, payment=150.0)
bm.mission_state = MissionState.LEAD_INCOMING
bm.current_lead  = lead
ok = bm.accept_lead(em, tm)
assert not ok
n = bm.pop_notifications()[0]
assert "barillet" in n.text.lower() or "epuis" in n.text.lower(), n.text
print(f"PASS – {n.text}")

# ── Test 3 : stock cap without office ─────────────────────────────────────
print("\n=== Test 3 : Achat barillets + plafond sans atelier ===")
tm, em, bm, mm = setup()
bm.buy_barillets(em)
bm.pop_notifications()
assert bm.stock_barillets == 5, bm.stock_barillets
ok2 = bm.buy_barillets(em)
assert not ok2, "2eme achat devrait etre bloque"
bm.pop_notifications()
print(f"PASS – stock={bm.stock_barillets}/5, 2eme achat bloque")

# ── Test 4 : mission consumes 1 barillet ──────────────────────────────────
print("\n=== Test 4 : Mission consomme 1 barillet ===")
bm.mission_state = MissionState.LEAD_INCOMING
bm.current_lead  = lead
sb = bm.stock_barillets
pb = em.business
bm.accept_lead(em, tm)
bm.pop_notifications()
assert bm.stock_barillets == sb - 1
assert abs((em.business - pb) - lead.net_gain) < 0.01
print(f"PASS – stock {sb}->{bm.stock_barillets}, delta={em.business - pb:.2f}")

# ── Test 5 : office unlocks unlimited stock ───────────────────────────────
print("\n=== Test 5 : Atelier = stock illimite ===")
tm, em, bm, mm = setup()
bm.rent_office(em)
bm.pop_notifications()
bm.buy_barillets(em)
bm.pop_notifications()
ok = bm.buy_barillets(em)
assert ok and bm.stock_barillets == 10
bm.pop_notifications()
print(f"PASS – stock={bm.stock_barillets} (pas de plafond avec atelier)")

# ── Test 6 : office rent charged to Pro every 30 days ────────────────────
print("\n=== Test 6 : Loyer atelier debite sur compte Pro tous les 30 jours ===")
tm2, em2, bm2, mm2 = setup()
bm2.rent_office(em2)
bm2.pop_notifications()
pro_after_first = em2.business   # 5000 - 500 (kit) - 500 (first rent)

rent_notifs = []
def on_midnight():
    em2.on_midnight()
    em2.pop_notifications()
    bm2.on_midnight(em2)
    for n in bm2.pop_notifications():
        rent_notifs.append(n)

tm2.on_midnight(on_midnight)

# After 29 days: no rent yet (business account unchanged by rent)
tm2.advance_minutes(29 * 24 * 60)
assert em2.business == pro_after_first, (
    f"Expected {pro_after_first}, got {em2.business}"
)
pro_at_29 = em2.business

# Day 30: rent fires
tm2.advance_minutes(24 * 60)
loyer_notifs = [n for n in rent_notifs if "loyer" in n.text.lower()]
assert loyer_notifs, f"No loyer notification: {rent_notifs}"
assert em2.business == pro_at_29 - 500, (
    f"Expected {pro_at_29 - 500}, got {em2.business}"
)
print(f"PASS – {loyer_notifs[-1].text}")
print(f"PASS – pro {pro_at_29:.0f} -> {em2.business:.0f} (loyer -500 sur compte Pro)")

# ── Test 7 : daily marketing budget deducted from Pro ────────────────────
print("\n=== Test 7 : Budget pub debite sur Pro a minuit ===")
_, em3, _, mm3 = setup()
mm3.daily_budget = 50.0
pb3 = em3.business
notifs3 = mm3.on_midnight(em3)
assert em3.business == pb3 - 50.0
assert any("pub" in n.text.lower() or "marketing" in n.text.lower() for n in notifs3)
print(f"PASS – {notifs3[0].text}")

print("\n=== TOUS LES TESTS PASSES ===")
