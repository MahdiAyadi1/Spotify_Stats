import { describe, expect, it } from "vitest";
import { formatCount, formatListeningTime } from "../format";

describe("formatListeningTime", () => {
  it("shows minutes only under an hour and drops the seconds", () => {
    expect(formatListeningTime(0)).toBe("0 min");
    expect(formatListeningTime(59_999)).toBe("0 min");
    expect(formatListeningTime(45 * 60_000)).toBe("45 min");
  });

  it("shows hours and zero-padded minutes from one hour", () => {
    expect(formatListeningTime(3_600_000)).toBe("1 h 00 min");
    expect(formatListeningTime(5_445_000)).toBe("1 h 30 min");
  });

  it("separates the thousands of hours", () => {
    expect(formatListeningTime((1_234 * 60 + 5) * 60_000)).toBe("1,234 h 05 min");
  });
});

describe("formatCount", () => {
  it("separates the thousands", () => {
    expect(formatCount(1_234_567)).toBe("1,234,567");
  });
});
