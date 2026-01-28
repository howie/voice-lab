class MockService:
    def __init__(self):
        self._accumulated_input_transcript = ""

    def handle_text(self, text):
        # The logic from gemini_realtime.py
        if text and text not in self._accumulated_input_transcript:
            self._accumulated_input_transcript += text
            print(f"Accepted: '{text}'. Total: '{self._accumulated_input_transcript}'")
        else:
            print(f"Skipped: '{text}'. Total: '{self._accumulated_input_transcript}'")

service = MockService()

print("--- Test Case 1: Repeated words ---")
service.handle_text("No")
service.handle_text(" No")
service.handle_text(" No") # Expected: "No No No", Actual: Skipped because " No" is in "No No"

service._accumulated_input_transcript = ""
print("\n--- Test Case 2: Common words ---")
service.handle_text("A cat")
service.handle_text(" is")
service.handle_text(" a")  # " a" is in "A cat is" (substring 'a ' reversed? no)
# " a" is in "A cat is" -> "c[a ]t" -> Yes, 'a ' is in 'cat '.
# So " a" will be skipped!
service.handle_text(" cat")

service._accumulated_input_transcript = ""
print("\n--- Test Case 3: Proper Deltas ---")
service.handle_text("Hel")
service.handle_text("lo") # "lo" not in "Hel" -> "Hello"
service.handle_text(" World") # " World" not in "Hello" -> "Hello World"
