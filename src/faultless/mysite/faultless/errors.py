# define a error

class Error:
    def __init__(self, message, original, corrected, p_location, s_location):
        self.message = message
        self.original = original
        self.corrected = corrected
        self.p_location = p_location
        self.s_location = s_location
    
