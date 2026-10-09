print("[Module] Test File")
def set():
  global command
  command = input("You>")

while True:
  set()
  if command == "exit":
    print("Bye")
    break
  if command == "salut":
    print("Salut")
