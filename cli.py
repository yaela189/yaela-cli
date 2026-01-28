import pandas as pd
import gspread
import webbrowser
import os
import sys
from time import sleep

# ספריות עיצוב
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import print as rprint
from rich.layout import Layout

# --- תיקון עברית ---
try:
    from bidi.algorithm import get_display
except ImportError:
    def get_display(text): return text

# --- הגדרות ---
MASTER_SHEET_ID = '1ihMDbc720k2VZZVpx2TskyOAuX8YWBJpC9Cc4kI0804'
SHEET_NAME = "ראשי"

console = Console()

# --- פונקציות עזר ---

def fix_text(text):
    """מסדר עברית שתופיע נכון בטרמינל"""
    if not text: return ""
    return get_display(str(text))

def get_gc():
    return gspread.service_account(filename='service_account.json')

def load_data():
    """טוען נתונים"""
    # עדכון טקסט: מאגר מידע חטיבתי
    msg = fix_text("מתחבר למאגר המידע החטיבתי...")
    with console.status(f"[bold green]{msg}[/bold green]", spinner="dots"):
        try:
            gc = get_gc()
            sh = gc.open_by_key(MASTER_SHEET_ID)
            ws = sh.worksheet(SHEET_NAME)
            all_values = ws.get_all_values()
            
            if len(all_values) < 2:
                return pd.DataFrame()
                
            headers = all_values[0]
            data = all_values[1:]
            df = pd.DataFrame(data, columns=headers)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            err_msg = fix_text("שגיאה בטעינה:")
            console.print(f"[bold red]{err_msg}[/bold red] {e}")
            return pd.DataFrame()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_battalions(df):
    """מציג תפריט גדודים"""
    battalions = sorted(df['גדוד'].unique())
    
    clear_screen()
    
    # עדכון טקסט: מערכת יעלה
    title = fix_text("מערכת יעלה - שליטה חטיבתית 🛡️")
    rprint(Panel.fit(f"[bold cyan]{title}[/bold cyan]", border_style="cyan"))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column(fix_text("גדודים זמינים"), min_width=20, justify="right")
    
    for bat in battalions:
        table.add_row(fix_text(bat))
    
    console.print(table)
    
    exit_txt = fix_text("0. יציאה")
    rprint(f"[dim]{exit_txt}[/dim]")
    
    return battalions

def show_files(df, battalion):
    """מציג את הקבצים של הגדוד הנבחר - תצוגה נקייה"""
    bat_df = df[df['גדוד'] == battalion].reset_index(drop=True)
    
    clear_screen()
    
    title = fix_text(f"קבצי {battalion} 📂")
    rprint(Panel(f"[bold yellow]{title}[/bold yellow]", border_style="yellow"))
    
    table = Table(show_header=True, header_style="bold green")
    table.add_column(fix_text("שם הקובץ"), justify="right")
    table.add_column(fix_text("אפשרויות"), justify="right")
    
    options_map = {} 
    counter = 1
    
    for idx, row in bat_df.iterrows():
        fname = fix_text(row.get('שם_קובץ', 'ללא שם'))
        desc = fix_text(row.get('תיאור_קובץ', ''))
        
        actions_display = []
        
        # --- בניית הכפתורים ---
        if row.get('לינק_מערכת'):
            key = counter
            options_map[key] = row['לינק_מערכת']
            actions_display.append(f"[{key}] {fix_text('מערכת 🚀')}") 
            counter += 1
            
        if row.get('לינק_קובץ'):
            key = counter
            options_map[key] = row['לינק_קובץ']
            actions_display.append(f"[{key}] {fix_text('אקסל 📎')}")
            counter += 1
        
        if actions_display:
            actions_str = "  |  ".join(actions_display)
        else:
            actions_str = fix_text("אין לינקים")

        # הוספת השורה לטבלה
        table.add_row(fname, actions_str)
        
        # תיאור הקובץ
        if desc:
            table.add_row(f"[dim]└─ {desc}[/dim]", "")
            table.add_section() 

    console.print(table)
    
    back_txt = fix_text("0. חזרה לתפריט ראשי")
    rprint(f"\n[dim]{back_txt}[/dim]")
    
    return options_map

def find_battalion_by_input(user_input, battalions):
    """מוצא גדוד לפי המספר שהמשתמש הזין"""
    user_input = str(user_input).strip()
    
    if user_input in battalions:
        return user_input
        
    for bat in battalions:
        if user_input in str(bat):
            return bat
            
    return None

# --- הלוגיקה הראשית ---
def main():
    df = load_data()
    if df.empty:
        return

    while True:
        battalions = show_battalions(df)
        
        q_bat = fix_text("הקלד מספר גדוד")
        user_input = Prompt.ask(f"\n{q_bat}")
        
        if user_input == "0":
            bye = fix_text("להתראות! 👋")
            rprint(f"[bold red]{bye}[/bold red]")
            break
            
        selected_bat = find_battalion_by_input(user_input, battalions)
        
        if selected_bat:
            while True:
                link_map = show_files(df, selected_bat)
                
                if not link_map:
                    no_files = fix_text("אין קבצים לגדוד זה")
                    rprint(f"[red]{no_files}[/red]")
                    Prompt.ask("Enter...")
                    break
                
                q_file = fix_text("בחר מספר לפתיחה (0 לחזרה)")
                file_choice = IntPrompt.ask(f"\n{q_file}", default=0)
                
                if file_choice == 0:
                    break
                    
                if file_choice in link_map:
                    url = link_map[file_choice]
                    opening = fix_text("פותח בדפדפן...")
                    rprint(f"[green]{opening}[/green] {url}")
                    webbrowser.open(url)
                    sleep(1)
                else:
                    err = fix_text("בחירה לא חוקית")
                    rprint(f"[red]{err}[/red]")
                    sleep(1)
        else:
            err_bat = fix_text("גדוד לא נמצא")
            rprint(f"[red]{err_bat}[/red]")
            sleep(1.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExit...")