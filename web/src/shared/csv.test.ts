import { describe, expect, it } from "vitest";
import { parseCsv, toCsv } from "./csv";

describe("csv", () => {
  it("parses quoted cells with commas, quotes and newlines", () => {
    const rows = parseCsv('﻿name,note\n"Ada, L","said ""hi""\nthen left"\r\n');

    expect(rows).toEqual([
      ["name", "note"],
      ["Ada, L", 'said "hi"\nthen left'],
    ]);
  });

  it("drops blank lines", () => {
    expect(parseCsv("a,b\n\n , \n1,2")).toEqual([
      ["a", "b"],
      ["1", "2"],
    ]);
  });

  it("round-trips through toCsv", () => {
    const rows = [
      ["Region", "Notes"],
      ["Coast", 'Storm, "closures"'],
    ];

    expect(parseCsv(toCsv(rows))).toEqual(rows);
  });
});
