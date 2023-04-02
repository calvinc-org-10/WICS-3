
    /*!
    * Serialize all form data into an object
    * (c) 2021 Chris Ferdinandi, MIT License, https://gomakethings.com
    * @param  {FormData} data The FormData object to serialize
    * @return {String}        The serialized form data
    */
    function serialize(elmnts) {
        let retStr = ''
        // let obj = {};
        for (let theelmnt of elmnts) {
            retStr += theelmnt.name + "='" + theelmnt.value + "';"
        }
        return retStr;
    }

//-------------------------------
//-------------------------------
//-------------------------------


//-------------------------------

    class MathParser {
        _CONSTANTS = {"pi": Math.PI, "e": Math.E, "phi": (1 + 5**0.5) / 2}

        _FUNCTIONS = {
            "abs": Math.abs,
            "acos": Math.acos,
            "asin": Math.asin,
            "atan": Math.atan,
            "atan2": Math.atan2,
            "ceil": Math.ceil,
            "cos": Math.cos,
            "cosh": Math.cosh,
            "degrees": Math.degrees,
            "exp": Math.exp,
            "fabs": Math.fabs,
            "floor": Math.floor,
            "fmod": Math.fmod,
            "frexp": Math.frexp,
            "hypot": Math.hypot,
            "ldexp": Math.ldexp,
            "log": Math.log,
            "log10": Math.log10,
            "modf": Math.modf,
            "pow": Math.pow,
            "radians": Math.radians,
            "sin": Math.sin,
            "sinh": Math.sinh,
            "sqrt": Math.sqrt,
            "tan": Math.tan,
            "tanh": Math.tanh,
        }

        constructor(expression, in_vars = None) {
            self.string = string
            self.index = 0
            self.in_vars = {} if in_vars == None else in_vars.copy()
            for constant in _CONSTANTS.keys():
                if self.in_vars.get(constant) != None:
                    raise NameError("Cannot redefine the value of " + constant)    
        }

        def getValue(self):
        value = self.parseExpression()
        self.skipWhitespace()

        if self.hasNext():
            raise SyntaxError(
                "Unexpected character found: '"
                + self.peek()
                + "' at index "
                + str(self.index)
            )
        return value

    def peek(self):
        return self.string[self.index : self.index + 1]

    def hasNext(self):
        return self.index < len(self.string)

    def isNext(self, value):
        return self.string[self.index : self.index + len(value)] == value

    def popIfNext(self, value):
        if self.isNext(value):
            self.index += len(value)
            return True
        return False

    def popExpected(self, value):
        if not self.popIfNext(value):
            raise SyntaxError("Expected '" + value + "' at index " + str(self.index))

    def skipWhitespace(self):
        while self.hasNext():
            if self.peek() in " \t\n\r":
                self.index += 1
            else:
                return

    def parseExpression(self):
        return self.parseAddition()

    def parseAddition(self):
        values = [self.parseMultiplication()]

        while True:
            self.skipWhitespace()
            char = self.peek()

            if char == "+":
                self.index += 1
                values.append(self.parseMultiplication())
            elif char == "-":
                self.index += 1
                values.append(-1 * self.parseMultiplication())
            else:
                break

        return sum(values)

    def parseMultiplication(self):
        values = [self.parseParenthesis()]

        while True:
            self.skipWhitespace()
            char = self.peek()

            if char == "*":
                self.index += 1
                values.append(self.parseParenthesis())
            elif char == "/":
                div_index = self.index
                self.index += 1
                denominator = self.parseParenthesis()

                if denominator == 0:
                    raise ZeroDivisionError(
                        "Division by 0 kills baby whales (occured at index "
                        + str(div_index)
                        + ")"
                    )
                values.append(1.0 / denominator)
            else:
                break

        value = 1.0

        for factor in values:
            value *= factor
        return value

    def parseParenthesis(self):
        self.skipWhitespace()
        char = self.peek()

        if char == "(":
            self.index += 1
            value = self.parseExpression()
            self.skipWhitespace()

            if self.peek() != ")":
                raise SyntaxError(
                    "No closing parenthesis found at character " + str(self.index)
                )
            self.index += 1
            return value
        else:
            return self.parseNegative()

    def parseArguments(self):
        args = []
        self.skipWhitespace()
        self.popExpected("(")
        while not self.popIfNext(")"):
            self.skipWhitespace()
            if len(args) > 0:
                self.popExpected(",")
                self.skipWhitespace()
            args.append(self.parseExpression())
            self.skipWhitespace()
        return args

    def parseNegative(self):
        self.skipWhitespace()
        char = self.peek()

        if char == "-":
            self.index += 1
            return -1 * self.parseParenthesis()
        else:
            return self.parseValue()

    def parseValue(self):
        self.skipWhitespace()
        char = self.peek()

        if char in "0123456789.":
            return self.parseNumber()
        else:
            return self.parseVariable()

    def parseVariable(self):
        self.skipWhitespace()
        var = []
        while self.hasNext():
            char = self.peek()

            if char.lower() in "_abcdefghijklmnopqrstuvwxyz0123456789":
                var.append(char)
                self.index += 1
            else:
                break
        var = "".join(var)

        function = _FUNCTIONS.get(var.lower())
        if function != None:
            args = self.parseArguments()
            return float(function(*args))

        constant = _CONSTANTS.get(var.lower())
        if constant != None:
            return constant

        value = self.in_vars.get(var, None)
        if value != None:
            return float(value)

        raise NameError("Unrecognized variable: '" + var + "'")

    def parseNumber(self):
        self.skipWhitespace()
        strValue = ""
        decimal_found = False
        char = ""

        while self.hasNext():
            char = self.peek()

            if char == ".":
                if decimal_found:
                    raise SyntaxError(
                        "Found an extra period in a number at character "
                        + str(self.index)
                        + ". Are you European?"
                    )
                decimal_found = True
                strValue += "."
            elif char in "0123456789":
                strValue += char
            else:
                break
            self.index += 1

        if len(strValue) == 0:
            if char == "":
                raise SyntaxError("Unexpected end found")
            else:
                raise SyntaxError(
                    "I was expecting to find a number at character "
                    + str(self.index)
                    + " but instead I found a '"
                    + char
                    + "'. What's up with that?"
                )

        return float(strValue)

    }

    function evaluate(expression, in_vars = None) {
        try {
            pars = MathParser(expression, in_vars)
            value = pars.getValue()
        } catch {
            value = NaN
        }

        if (isNaN(value)) {
            return value
        }
        // Return an integer type if the answer is an integer
        if (value.isInteger()) {
            return parseInt(value)
        }
        // If Python made some silly precision error like x.99999999999996, just return x+1 as an integer
        epsilon = 0.0000000001
        if (parseInt(value + epsilon) != parseInt(value)) {
            return parseInt(value + epsilon)
        }
        if (parseInt(value - epsilon) != parseInt(value)) {
            return parseInt(value)
        }
        return value
    }
    
    function EvalExpr(expr) {
        try {
            ev = eval(expr)   // yes, I know it's dangerous.  I'll do better when I can
        } catch {
            ev = "????"
        }
        return ev;
    }

