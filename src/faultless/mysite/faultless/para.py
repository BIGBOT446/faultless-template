class Paragraph:
    def __init__(self):
        self.body = None
        self.errors = []
        self.error_num = len(self.errors)

    def add_error(self, error):
        self.errors.append(error)
    
    def add_body(self, body):
        self.body = body
    
