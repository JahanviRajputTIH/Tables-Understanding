import json
import re
from bs4 import BeautifulSoup
import numpy as np
from tqdm import tqdm

def extract_otsl_with_content(html_string):
    """
    Converts an HTML table into an OTSL matrix with content at the correct positions,
    handling complex structures with rowspan and colspan.
    """
    soup = BeautifulSoup(html_string, 'html.parser')
    table = soup.find('table')

    if not table:
        return "<otsl> </otsl>"  # Return empty OTSL if no table exists

    rows = table.find_all('tr')

    # Step 1: Compute Actual Row Count (`R`) and Column Count (`C`)
    row_spans = []  # Track ongoing rowspan usage
    R = len(rows)  # Base row count
    C = max(sum(int(cell.get('colspan', 1)) for cell in row.find_all(['td', 'th'])) for row in rows)

    # Adjust R based on `rowspan`
    for row in rows:
        row_span_count = [int(cell.get('rowspan', 1)) for cell in row.find_all(['td', 'th'])]
        if row_span_count:
            max_rowspan = max(row_span_count)
            if max_rowspan > 1:
                R += (max_rowspan - 1)

    # Step 2: Initialize OTSL Matrix and Cell Map
    otsl_matrix = [['<ecel>' for _ in range(C)] for _ in range(R)]
    cell_map = np.zeros((R, C), dtype=int)  # Tracks occupied cells

    row_idx = 0  # Tracks the actual row index
    for row in rows:
        col_idx = 0
        while row_idx < R and np.any(cell_map[row_idx]):  # Skip already occupied rows
            row_idx += 1

        for cell in row.find_all(['td', 'th']):
            while col_idx < C and cell_map[row_idx][col_idx] == 1:
                col_idx += 1

            rowspan = int(cell.get('rowspan', 1))
            colspan = int(cell.get('colspan', 1))

            if row_idx >= R or col_idx >= C:
                continue  # Skip if indices go out of bounds

            cell_text = cell.get_text(strip=True).replace(" ", "_")
            otsl_matrix[row_idx][col_idx] = f'<fcel> {cell_text}' if cell_text else '<ecel>'

            # Fill merged cells
            for c in range(1, colspan):
                if col_idx + c < C:
                    otsl_matrix[row_idx][col_idx + c] = '<lcel>'

            for r in range(1, rowspan):
                if row_idx + r < R:
                    otsl_matrix[row_idx + r][col_idx] = '<ucel>'
                    for c in range(1, colspan):
                        if col_idx + c < C:
                            otsl_matrix[row_idx + r][col_idx + c] = '<xcel>'

            # Mark occupied positions
            for r in range(rowspan):
                for c in range(colspan):
                    if row_idx + r < R and col_idx + c < C:
                        cell_map[row_idx + r][col_idx + c] = 1

            col_idx += colspan  # Move to next column after colspan width

        row_idx += 1  # Move to the next row

    # Convert matrix to OTSL string
    otsl_string = " ".join([" ".join(row) + " <nl>" for row in otsl_matrix]).strip()
    return otsl_string

html_string = "<table><tr><td></td><td>2008</td><td>2007</td><td>2006</td></tr><tr><td>Cash flows provided by (used for):</td><td></td><td></td><td></td></tr><tr><td>Operating activities</td><td>$455.7</td><td>$381.5</td><td>$267.5</td></tr><tr><td>Investing activities</td><td>(580.7)</td><td>(380.5)</td><td>(166.0)</td></tr><tr><td>Financing activities</td><td>299.4</td><td>(24.5)</td><td>(53.6)</td></tr><tr><td>Net increase (decrease) in cash and cash equivalents</td><td>174.4</td><td>(23.5)</td><td>47.9</td></tr><tr><td>Cash and cash equivalents beginning of year</td><td>55.5</td><td>79.0</td><td>31.1</td></tr><tr><td>Cash and cash equivalents end of year</td><td>$229.9</td><td>$55.5</td><td>$79.0</td></tr></table>"
print(extract_otsl_with_content(html_string))
