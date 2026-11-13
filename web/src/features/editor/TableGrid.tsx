import { useEffect, useState } from "react";
import type { Block, BlockPatch } from "../../shared/api/client";
import { downloadFile, parseCsv, toCsv } from "../../shared/csv";
import { Button } from "../../shared/ui";
import "./table.css";

export function TableGrid({ block, onSave }: { block: Block; onSave: (patch: BlockPatch) => void }) {
  const [rows, setRows] = useState(() => parseCsv(block.table_csv ?? ""));
  const width = Math.max(0, ...rows.map((r) => r.length));

  useEffect(() => setRows(parseCsv(block.table_csv ?? "")), [block.table_csv]);

  const setCell = (r: number, c: number, value: string) =>
    setRows((current) => current.map((row, i) => (i === r ? Object.assign([...row], { [c]: value }) : row)));

  const commit = () => {
    const csv = toCsv(rows.map((row) => [...row, ...Array(width - row.length).fill("")]));
    if (csv !== block.table_csv) onSave({ table_csv: csv });
  };

  return (
    <div className="table-block">
      {block.flags.length > 0 && (
        <ul className="table-flags" aria-label="Table checks">
          {block.flags.map((flag) => (
            <li key={flag}>{flag}</li>
          ))}
        </ul>
      )}
      <div className="table-scroll">
        <table className="table-grid">
          <tbody>
            {rows.map((row, r) => (
              <tr key={r}>
                {Array.from({ length: width }, (_, c) => (
                  <td key={c}>
                    <input
                      className={r === 0 ? "cell cell-head" : "cell"}
                      aria-label={`Row ${r + 1}, column ${c + 1}`}
                      value={row[c] ?? ""}
                      onChange={(e) => setCell(r, c, e.target.value)}
                      onBlur={commit}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Button variant="quiet" onClick={() => downloadFile("table.csv", block.table_csv ?? "", "text/csv")}>
        Download CSV
      </Button>
    </div>
  );
}
