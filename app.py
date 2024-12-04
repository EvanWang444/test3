import requests
from bs4 import BeautifulSoup
import sqlite3
from tkinter import Tk, Label, Entry, Button, messagebox, ttk, scrolledtext
from tkinter.constants import N, S, E, W

DATABASE = "contacts.db"

def setup_database() -> None:
    """初始化 SQLite 資料庫，建立 contacts 資料表。"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            iid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()

def save_to_database(data: list[dict]) -> None:
    """將聯絡資訊保存到 SQLite 資料庫中。

    Args:
        data (list[dict]): 要儲存的聯絡人資料清單。
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for item in data:
        try:
            cursor.execute("""
                INSERT INTO contacts (name, title, email) 
                VALUES (?, ?, ?)
            """, (item["name"], item["title"], item["email"]))
        except sqlite3.IntegrityError:
            pass  
    conn.commit()
    conn.close()

def scrape_contacts(url: str) -> list[dict]:
    """從指定 URL 中抓取聯絡資訊。

    Args:
        url (str): 要爬取的目標網址。

    Returns:
        list[dict]: 抓取到的聯絡資訊清單。
    """
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        messagebox.showerror("錯誤", f"無法取得資料：{e}")
        return []

    members = []
    for member in soup.find_all('div', class_='member_name'):
        try:
            name = member.find('a').text.strip()

            position_block = member.find_next('div', class_='member_info_area')
            position = position_block.find('div', class_='member_info_content').text.strip()
 
            email_block = position_block.find_next('div', class_='member_info_area').find_next('div', class_='member_info_area')
            email = email_block.find('a')['href'].replace('mailto:', '').strip()
 
            members.append({'name': name, 'title': position, 'email': email})
        except AttributeError:
            continue   
    return members
 
def display_contacts(data: list[dict], output: scrolledtext.ScrolledText) -> None:
    """在 Tkinter 的 ScrolledText 中顯示聯絡資訊。

    Args:
        data (list[dict]): 聯絡資訊清單。
        output (ScrolledText): 用於顯示聯絡資訊的 ScrolledText 元件。
    """
    output.delete("1.0", "end")
    for contact in data:
        output.insert("end", f"姓名: {contact['name']}\n")
        output.insert("end", f"職稱: {contact['title']}\n")
        output.insert("end", f"Email: {contact['email']}\n")
        output.insert("end", "-" * 30 + "\n")
 
def main():
    """執行主程式，建立 Tkinter GUI 界面。"""
    setup_database()

    def on_fetch():
        url = url_entry.get().strip()
        if not url:
            messagebox.showerror("錯誤", "請輸入有效的 URL")
            return

        contacts = scrape_contacts(url)
        if contacts:
            save_to_database(contacts)
            display_contacts(contacts, output_text)
            messagebox.showinfo("成功", f"已成功抓取 {len(contacts)} 筆資料！")
 
    root = Tk()
    root.title("聯絡資訊爬蟲")
    root.geometry("640x480")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
 
    Label(root, text="目標 URL：").grid(row=0, column=0, sticky=E, padx=5, pady=5)
    url_entry = Entry(root)
    url_entry.grid(row=0, column=1, sticky=W+E, padx=5, pady=5)
    url_entry.insert(0, "https://csie.ncut.edu.tw/content.php?key=86OP82WJQO")
 
    Button(root, text="抓取", command=on_fetch).grid(row=0, column=2, padx=5, pady=5)
 
    output_text = scrolledtext.ScrolledText(root, wrap="word")
    output_text.grid(row=1, column=0, columnspan=3, sticky=N+S+E+W, padx=5, pady=5)

    root.mainloop()

main()