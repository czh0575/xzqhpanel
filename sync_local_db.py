"""Rebuild the local SQLite database from the bundled 1980–2026 workbook."""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'resources' / '县级行政区划1980-2026.xlsx'
DATABASE = ROOT / 'resources' / 'adminarea.sqlite3'

def main():
    frame = pd.read_excel(SOURCE)
    frame = frame.rename(columns={
        frame.columns[0]: 'AreaCode',
        frame.columns[1]: 'Level',
        frame.columns[2]: 'Catalog',
    })
    frame['AreaCode'] = frame['AreaCode'].astype('Int64').astype(str)
    with sqlite3.connect(DATABASE) as connection:
        frame.to_sql('adminarea', connection, index=False, if_exists='replace')
        connection.execute('CREATE INDEX IF NOT EXISTS idx_adminarea_level ON adminarea(Level)')
    print(f'Updated {DATABASE} with {len(frame)} records ({frame.columns[3]}–{frame.columns[-1]}).')

if __name__ == '__main__':
    main()
