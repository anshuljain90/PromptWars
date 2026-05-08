import { describe, expect, it } from "vitest";
import { cn } from "@/lib/cn";

describe("cn() class merge", () => {
  it("joins multiple classes", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("dedupes conflicting Tailwind classes (last wins)", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });

  it("ignores falsy values", () => {
    expect(cn("a", false && "b", null, undefined, "c")).toBe("a c");
  });
});
