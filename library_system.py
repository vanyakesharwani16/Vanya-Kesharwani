"""
Library Book Issue Management System
Course: Computational Thinking and Programming (2026CSAE100)
Bennett University — School of Computer Science Engineering and Technology
"""

import csv
import os
from datetime import date, datetime, timedelta

# System Constants
LOAN_DAYS = 14
FINE_PER_DAY = 2
MAX_BOOKS = 3
HIGH_DEMAND = 9
LOW_DEMAND = 2

BOOKS_FILE = "books.csv"
ISSUES_FILE = "issues.csv"
REPORT_FILE = "report.txt"


# --- Object Models (EL Activity 6: Object Modeling with Paper Cards) ---
class LibraryItem:
    """Base entity representing a catalogued library resource."""
    def __init__(self, item_id, title, category):
        self.item_id = item_id.strip().upper()
        self.title = title.strip()
        self.category = category.strip().title()


class Book(LibraryItem):
    """Represents a physical book title with multiple copies."""
    def __init__(self, book_id, title, author, category, total_copies):
        super().__init__(book_id, title, category)
        self.author = author.strip()
        self.total_copies = int(total_copies)

    def to_dict(self):
        return {
            "book_id": self.item_id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "total_copies": self.total_copies,
        }


class Member:
    """Represents a student library borrower."""
    def __init__(self, member_id, active_books=None):
        self.member_id = member_id.strip().upper()
        self.active_books = set(active_books) if active_books else set()

    def can_borrow(self):
        return len(self.active_books) < MAX_BOOKS

    def holds_book(self, book_id):
        return book_id.strip().upper() in self.active_books


class IssueRecord:
    """Represents an individual book borrowing transaction."""
    def __init__(self, member_id, book_id, issue_date, due_date, return_date=None, fine=0):
        self.member_id = member_id.strip().upper()
        self.book_id = book_id.strip().upper()
        self.issue_date = issue_date
        self.due_date = due_date
        self.return_date = return_date
        self.fine = int(fine)

    def is_active(self):
        return self.return_date is None

    def to_dict(self):
        return {
            "member_id": self.member_id,
            "book_id": self.book_id,
            "issue_date": self.issue_date.strftime("%Y-%m-%d"),
            "due_date": self.due_date.strftime("%Y-%m-%d"),
            "return_date": self.return_date.strftime("%Y-%m-%d") if self.return_date else "",
            "fine": str(self.fine),
        }


# --- Data Persistence Module ---
def load_books(filename=BOOKS_FILE):
    """Loads books from CSV into a dictionary keyed by book_id."""
    if not os.path.exists(filename):
        return {}
    books = {}
    with open(filename, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                b_id = row["book_id"].strip().upper()
                if not b_id:
                    continue
                books[b_id] = {
                    "book_id": b_id,
                    "title": row["title"].strip(),
                    "author": row["author"].strip(),
                    "category": row["category"].strip().title(),
                    "total_copies": int(row["total_copies"]),
                }
            except (ValueError, KeyError, TypeError):
                continue
    return books


def load_issues(filename=ISSUES_FILE):
    """Loads issue records from CSV, skipping corrupt rows."""
    if not os.path.exists(filename):
        return []
    issues = []
    with open(filename, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                m_id = row["member_id"].strip().upper()
                b_id = row["book_id"].strip().upper()
                i_date = datetime.strptime(row["issue_date"].strip(), "%Y-%m-%d").date()
                d_date = datetime.strptime(row["due_date"].strip(), "%Y-%m-%d").date()
                r_raw = row.get("return_date", "").strip()
                r_date = datetime.strptime(r_raw, "%Y-%m-%d").date() if r_raw else None
                fine = int(row.get("fine", 0) or 0)
                issues.append({
                    "member_id": m_id,
                    "book_id": b_id,
                    "issue_date": i_date,
                    "due_date": d_date,
                    "return_date": r_date,
                    "fine": fine,
                })
            except (ValueError, KeyError, TypeError):
                continue
    return issues


def save_issues(issues, filename=ISSUES_FILE):
    """Writes all issue records back to CSV."""
    fieldnames = ["member_id", "book_id", "issue_date", "due_date", "return_date", "fine"]
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in issues:
            writer.writerow({
                "member_id": rec["member_id"],
                "book_id": rec["book_id"],
                "issue_date": rec["issue_date"].strftime("%Y-%m-%d"),
                "due_date": rec["due_date"].strftime("%Y-%m-%d"),
                "return_date": rec["return_date"].strftime("%Y-%m-%d") if rec["return_date"] else "",
                "fine": rec["fine"],
            })


# --- Input Validation Helpers ---
def read_text(prompt):
    """Reads non-empty normalized text input."""
    while True:
        val = input(prompt).strip().upper()
        if val:
            return val
        print("Input cannot be empty.")


def read_date(prompt, reference_today=None):
    """Reads and validates a YYYY-MM-DD date not in the future."""
    today = reference_today or date.today()
    while True:
        raw = input(prompt).strip()
        try:
            parsed = datetime.strptime(raw, "%Y-%m-%d").date()
            if parsed > today:
                print("Date cannot be in the future.")
                continue
            return parsed
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD (e.g. 2026-10-24).")


# --- Core Library Operations ---
def copies_available(book_id, books, issues):
    """Calculates available copies = total copies - active issues."""
    total = books[book_id]["total_copies"]
    active = sum(1 for rec in issues if rec["book_id"] == book_id and rec["return_date"] is None)
    return total - active


def member_active_books(member_id, issues):
    """Returns set of book_ids currently held by a member."""
    return {rec["book_id"] for rec in issues if rec["member_id"] == member_id and rec["return_date"] is None}


def calculate_fine(due_date, return_date):
    """Computes late fine at Rs. 2 per overdue day."""
    if return_date <= due_date:
        return 0
    return (return_date - due_date).days * FINE_PER_DAY


def issue_book(books, issues, member_id=None, book_id=None, issue_dt=None):
    """Issues a book if member limit (<3) and stock (>0) allow."""
    if member_id is None:
        member_id = read_text("Member ID: ")
    else:
        member_id = member_id.strip().upper()

    while True:
        if book_id is None:
            b_id = read_text("Book ID: ")
        else:
            b_id = book_id.strip().upper()
        if b_id in books:
            book_id = b_id
            break
        print("Book ID not found in catalogue.")
        if book_id is not None:
            return False, "Book ID not found in catalogue."

    member = Member(member_id, member_active_books(member_id, issues))
    if not member.can_borrow():
        msg = f"Limit reached: a member can hold only {MAX_BOOKS} books at a time."
        print(msg)
        return False, msg

    if member.holds_book(book_id):
        msg = "Member already holds an active copy of this book."
        print(msg)
        return False, msg

    if copies_available(book_id, books, issues) <= 0:
        msg = "No copies available right now. Please try later."
        print(msg)
        return False, msg

    if issue_dt is None:
        issue_dt = read_date("Issue date (YYYY-MM-DD): ")

    due_dt = issue_dt + timedelta(days=LOAN_DAYS)
    rec = IssueRecord(member_id, book_id, issue_dt, due_dt)
    issues.append({
        "member_id": rec.member_id,
        "book_id": rec.book_id,
        "issue_date": rec.issue_date,
        "due_date": rec.due_date,
        "return_date": rec.return_date,
        "fine": rec.fine,
    })
    save_issues(issues)
    msg = f"Book issued: {books[book_id]['title']}. Due date: {due_dt.strftime('%Y-%m-%d')}."
    print(msg)
    return True, msg


def return_book(books, issues, member_id=None, book_id=None, return_dt=None):
    """Processes book return, validates date, computes fine, updates CSV."""
    if member_id is None:
        member_id = read_text("Member ID: ")
    else:
        member_id = member_id.strip().upper()

    if book_id is None:
        book_id = read_text("Book ID: ")
    else:
        book_id = book_id.strip().upper()

    target_rec = None
    for rec in issues:
        if rec["member_id"] == member_id and rec["book_id"] == book_id and rec["return_date"] is None:
            target_rec = rec
            break

    if target_rec is None:
        msg = "No active issue found for this member and book."
        print(msg)
        return False, msg

    while True:
        r_dt = return_dt if return_dt is not None else read_date("Return date (YYYY-MM-DD): ")
        if r_dt < target_rec["issue_date"]:
            print("Return date cannot be before the issue date.")
            if return_dt is not None:
                return False, "Return date cannot be before the issue date."
            continue
        break

    fine = calculate_fine(target_rec["due_date"], r_dt)
    target_rec["return_date"] = r_dt
    target_rec["fine"] = fine
    save_issues(issues)
    msg = f"Book returned. Fine: Rs. {fine}"
    print(msg)
    return True, msg


def view_catalogue(books, issues):
    """Displays formatted catalogue with total and available copies."""
    print(f"\n{'ID':<6} {'Title':<32} {'Category':<18} {'Avail/Total'}")
    print("-" * 72)
    for b_id, info in sorted(books.items()):
        avail = copies_available(b_id, books, issues)
        print(f"{b_id:<6} {info['title']:<32} {info['category']:<18} {avail}/{info['total_copies']}")


# --- Computational Analytics & Rule-Based Recommendation Engine ---
def period_counts(books, issues, end_date, days):
    """Counts issues per book and per category within `days` up to `end_date`."""
    start_date = end_date - timedelta(days=days - 1)
    book_counts = {b_id: 0 for b_id in books}
    cat_counts = {}
    total = 0
    for rec in issues:
        if start_date <= rec["issue_date"] <= end_date:
            b_id = rec["book_id"]
            if b_id in books:
                book_counts[b_id] += 1
                cat = books[b_id]["category"]
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
                total += 1
    return total, book_counts, cat_counts


def recommend(books, issues, count_30):
    """Classifies each book into ADD COPIES / REVIEW / KEEP."""
    priority = {"ADD COPIES": 0, "REVIEW": 1, "KEEP": 2}
    recs = []
    for b_id, info in books.items():
        c = count_30.get(b_id, 0)
        avail = copies_available(b_id, books, issues)
        if c >= HIGH_DEMAND:
            decision = "ADD COPIES"
            note = "high demand"
        elif c <= LOW_DEMAND:
            decision = "REVIEW"
            note = "low demand"
        else:
            decision = "KEEP"
            note = "normal demand"
        if avail == 0:
            note += ", all copies issued"
        recs.append((info["title"], decision, c, note))
    recs.sort(key=lambda x: (priority[x[1]], -x[2], x[0]))
    return recs


def build_report(books, issues, save_to_file=True):
    """Generates full analytical report and saves to report.txt."""
    if not issues:
        return "No issue records available for analysis."

    end_date = max(rec["issue_date"] for rec in issues)
    total_7, _, _ = period_counts(books, issues, end_date, 7)
    total_30, count_30, cat_30 = period_counts(books, issues, end_date, 30)

    sorted_cats = sorted(cat_30.items(), key=lambda x: (-x[1], x[0]))
    cat_str = ", ".join(f"{cat} {cnt}" for cat, cnt in sorted_cats)

    sorted_books = sorted(count_30.items(), key=lambda x: (-x[1], books[x[0]]["title"]))
    most_id, most_cnt = sorted_books[0]
    least_id, least_cnt = sorted_books[-1]

    overdue_list = []
    for rec in issues:
        if rec["return_date"] is None and end_date > rec["due_date"]:
            late_days = (end_date - rec["due_date"]).days
            fine_due = late_days * FINE_PER_DAY
            overdue_list.append((late_days, rec["member_id"], books[rec["book_id"]]["title"], fine_due))
    overdue_list.sort(key=lambda x: (-x[0], x[1]))

    start_30 = end_date - timedelta(days=29)
    fine_collected = sum(
        rec["fine"] for rec in issues
        if rec["return_date"] is not None and start_30 <= rec["return_date"] <= end_date
    )

    lines = [
        f"===== LIBRARY ANALYSIS REPORT (up to {end_date.strftime('%Y-%m-%d')}) =====",
        "",
        f"Books issued - last 7 days: {total_7}, last 30 days: {total_30}",
        f"Issues by category (30 days): {cat_str}",
        f"Most issued : {books[most_id]['title']} ({most_cnt} issue(s))",
        f"Least issued: {books[least_id]['title']} ({least_cnt} issue(s))",
        "",
        f"Overdue books (not returned, past due date): {len(overdue_list)}",
    ]
    for late_days, m_id, title, fine_due in overdue_list:
        lines.append(f"  {m_id:<6} {title:<32} {late_days:>2} days late (fine so far Rs. {fine_due})")

    lines.append("")
    lines.append(f"Fine collected in last 30 days: Rs. {fine_collected}")
    lines.append("")
    lines.append("RECOMMENDATIONS FOR NEXT PURCHASE CYCLE")
    lines.append(f"{'Book':<32} {'Decision':<12} {'Issues':<8} {'Note'}")
    for title, decision, cnt, note in recommend(books, issues, count_30):
        lines.append(f"{title:<32} {decision:<12} {cnt:<8} {note}")

    report_text = "\n".join(lines)
    if save_to_file:
        with open(REPORT_FILE, mode="w", encoding="utf-8") as f:
            f.write(report_text + "\n")
    return report_text


def main():
    books = load_books()
    if not books:
        print("books.csv not found or empty. Please add it first.")
        return
    issues = load_issues()
    while True:
        print("\n===== LIBRARY BOOK ISSUE MANAGEMENT =====")
        print("1. Issue a book")
        print("2. Return a book")
        print("3. View catalogue")
        print("4. Generate analysis report")
        print("5. Exit")
        choice = input("Choose (1-5): ").strip()
        if choice == "1":
            issue_book(books, issues)
        elif choice == "2":
            return_book(books, issues)
        elif choice == "3":
            view_catalogue(books, issues)
        elif choice == "4":
            print("\n" + build_report(books, issues))
        elif choice == "5":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Enter 1-5.")


if __name__ == "__main__":
    main()
