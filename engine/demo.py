"""手动冒烟：打印一场 λ=1.8 vs 1.0 的全玩法概率。"""
from engine import predict


def main():
    r = predict(1.8, 1.0, handicap=-1)
    print("胜平负:", {k: round(v, 3) for k, v in r["spf"].items()})
    print("让球(主-1):", {k: round(v, 3) for k, v in r["handicap"].items()})
    print("总进球:", {k: round(v, 3) for k, v in r["total_goals"].items()})
    top_cs = sorted(r["correct_score"].items(), key=lambda x: -x[1])[:5]
    print("比分Top5:", [(k, round(v, 3)) for k, v in top_cs])
    print("半全场:", {k: round(v, 3) for k, v in r["half_full"].items()})


if __name__ == "__main__":
    main()
