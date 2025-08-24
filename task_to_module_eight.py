import pickle
from datetime import datetime, date, timedelta
from collections import UserDict

PICKLE_FILE = "addressbook.pkl"


def save_data(book: "AddressBook", filename: str = PICKLE_FILE) -> None:
    with open(filename, "wb") as f:
        pickle.dump(book, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_data(filename: str = PICKLE_FILE) -> "AddressBook":
    try:
        with open(filename, "rb") as f:
            data = pickle.load(f)
            return data if isinstance(data, AddressBook) else AddressBook()
    except (FileNotFoundError, EOFError):
        return AddressBook()


class Field:
    def __init__(self, value):
        self.value = value


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not isinstance(value, str):
            raise TypeError("Телефон повинен бути рядком з 10 цифр.")
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Номер телефону має складатися з 10 цифр.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        self.validate(value)
        super().__init__(value)

    @staticmethod
    def validate(value: str):
        if not isinstance(value, str):
            raise TypeError("Дата народження повинна бути у форматі DD.MM.YYYY.")
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Невірний формат дати. Використовуйте DD.MM.YYYY.")
        if parsed_date > date.today():
            raise ValueError("Дата народження не може бути в майбутньому.")

    @staticmethod
    def to_date(value: str) -> date:
        return datetime.strptime(value, "%d.%m.%Y").date()


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def change_phone(self, old, new):
        for i, p in enumerate(self.phones):
            if p.value == old:
                self.phones[i] = Phone(new)
                return
        raise ValueError("Старий номер не знайдено.")

    def add_birthday(self, birthday_str):
        if self.birthday is not None:
            raise ValueError("День народження вже додано.")
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        phones = ", ".join(p.value for p in self.phones) if self.phones else "—"
        birthday = self.birthday.value if self.birthday else "Немає"
        return f"{self.name.value}: {phones}; День народження: {birthday}"


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name) -> Record | None:
        return self.data.get(name)

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming = []
        for record in self.data.values():
            if record.birthday:
                bday_date = Birthday.to_date(record.birthday.value).replace(year=today.year)
                if bday_date < today:
                    bday_date = bday_date.replace(year=today.year + 1)
                delta = (bday_date - today).days
                if 0 <= delta <= 7:
                    # перенесення привітання з вихідних на понеділок
                    if bday_date.weekday() == 5:
                        bday_date += timedelta(days=2)
                    elif bday_date.weekday() == 6:
                        bday_date += timedelta(days=1)
                    upcoming.append({
                        "name": record.name.value,
                        "birthday": bday_date.strftime("%d.%m.%Y")
                    })
        return upcoming


def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError:
            return "Помилка: Контакт не знайдено."
        except IndexError:
            return "Помилка: Недостатньо аргументів."
        except KeyError:
            return "Помилка: Ключ не знайдено."
        except TypeError as e:
            return f"Помилка: {e}"
        except ValueError as e:
            return f"Помилка: {e}"
    return wrapper


def parse_input(user_input):
    parts = user_input.strip().split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    return command, args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Контакт оновлено."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Контакт додано."
    record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old, new = args
    record = book.find(name)
    record.change_phone(old, new)
    return "Номер змінено."


@input_error
def get_phones(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        return "Помилка: Контакт не знайдено."
    if not record.phones:
        return "У цього контакту немає номерів."
    return ", ".join(p.value for p in record.phones)


@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "Адресна книга порожня."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday_cmd(args, book: AddressBook):
    name, bday = args
    record = book.find(name)
    record.add_birthday(bday)
    return f"День народження для {name} додано."


@input_error
def show_birthday_cmd(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record.birthday:
        return f"День народження {name}: {record.birthday.value}"
    raise ValueError("День народження не знайдено.")


@input_error
def birthdays_cmd(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "Немає днів народження цього тижня."
    return "\n".join(f"{item['name']}: {item['birthday']}" for item in upcoming)


def main():
    book = load_data()
    print("Welcome to the assistant!")
    try:
        while True:
            user_input = input("Enter command: ")
            command, args = parse_input(user_input)

            if command in ["close", "exit"]:
                print("Good bye!")
                break
            elif command == "hello":
                print("How can I help you?")
            elif command == "add":
                print(add_contact(args, book))
            elif command == "change":
                print(change_contact(args, book))
            elif command == "phone":
                print(get_phones(args, book))
            elif command == "all":
                print(show_all(book))
            elif command == "add-birthday":
                print(add_birthday_cmd(args, book))
            elif command == "show-birthday":
                print(show_birthday_cmd(args, book))
            elif command == "birthdays":
                print(birthdays_cmd(args, book))
            else:
                print("Unknown command.")
    except KeyboardInterrupt:
        print("\nЗавершення роботи (Ctrl+C).")
    finally:
        # Збереження стану книги при будь-якому виході
        save_data(book)


if __name__ == "__main__":
    main()
