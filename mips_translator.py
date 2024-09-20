def translate_to_mips_advanced(c_code):
    # A dictionary mapping C operations to MIPS instructions
    op_map = {
        '+': 'add',
        '-': 'sub',
        '*': 'mul',
        '/': 'div',
        '&': 'and',
        '|': 'or',
        '^': 'xor',
        '<<': 'sll',
        '>>': 'srl'
    }

    immediate_op_map = {
        '+': 'addi',
        '-': 'subi'
    }

    condition_op_map = {
        '==': 'beq',
        '!=': 'bne',
        '<': 'blt',
        '<=': 'ble',
        '>': 'bgt',
        '>=': 'bge'
    }

    # Register allocation based on conventions
    register_count = 0
    registers = {}

    def allocate_register(var):
        nonlocal register_count
        if var not in registers:
            reg = f"$t{register_count % 10}"  # Reuse $t0-$t9
            registers[var] = reg
            register_count += 1
        return registers[var]

    mips_code = []
    lines = c_code.splitlines()
    in_main = False
    label_count = 0

    def new_label(base="label"):
        nonlocal label_count
        label_count += 1
        return f"{base}_{label_count}"

    false_label = None
    end_label = None

    for line in lines:
        line = line.strip()
        if 'int main' in line:
            in_main = True
            mips_code.append("main:")  # Label for the main function
            mips_code.append("    li $v0, 0")  # Initialize return value
            continue  # Skip the 'int main()' line
        if in_main:
            if line == '}':
                mips_code.append("    li $v0, 10")  # System call for exit
                mips_code.append("    syscall")  # Terminate the program
                in_main = False  # End of main
                continue

            # Process while loops
            if 'while' in line:
                # Extract condition inside the parentheses
                condition = line[line.find('(') + 1:line.find(')')].strip()
                loop_start_label = new_label("loop_start")
                loop_end_label = new_label("loop_end")
                mips_code.append(f"{loop_start_label}:")  # Loop start

                for op in condition_op_map:
                    if op in condition:
                        left_var, right_var = condition.split(op)
                        left_var = left_var.strip()
                        right_var = right_var.strip()

                        reg1 = allocate_register(left_var)
                        mips_code.append(f"    lw {reg1}, {left_var}")

                        # If right side is a variable or a digit
                        if right_var.isdigit():
                            reg2 = right_var
                        else:
                            reg2 = allocate_register(right_var)
                            mips_code.append(f"    lw {reg2}, {right_var}")

                        mips_code.append(f"    {condition_op_map[op]} {reg1}, {reg2}, {loop_end_label}  # while {left_var} {op} {right_var}")
                        break

            elif '}' in line and 'while' in line:
                # End of while loop
                mips_code.append(f"    j {loop_start_label}")  # Jump back to loop start
                mips_code.append(f"{loop_end_label}:")  # Loop end

            # Process if-else statements
            if 'if' in line:
                condition = line[line.find('(') + 1:line.find(')')].strip()
                for op in condition_op_map:
                    if op in condition:
                        left_var, right_var = condition.split(op)
                        left_var = left_var.strip()
                        right_var = right_var.strip()

                        reg1 = allocate_register(left_var)
                        mips_code.append(f"    lw {reg1}, {left_var}")

                        if right_var.isdigit():
                            reg2 = right_var
                        else:
                            reg2 = allocate_register(right_var)
                            mips_code.append(f"    lw {reg2}, {right_var}")

                        false_label = new_label("else")
                        mips_code.append(f"    {condition_op_map[op]} {reg1}, {reg2}, {false_label}  # if {left_var} {op} {right_var}")
                        end_label = new_label("end_if")  # Assign end label here
                        break

            elif 'else' in line:
                if end_label:
                    mips_code.append(f"    j {end_label}")  # Jump to end of if-else
                if false_label:
                    mips_code.append(f"{false_label}:")  # Label for false branch

            elif '{' in line or '}' in line:
                continue

            else:
                # Handle arithmetic/assignments in if-else/while loop body
                if '=' in line and ';' in line:
                    parts = line.strip(';').split('=')
                    left_var = parts[0].strip()
                    expression = parts[1].strip()

                    # Tokenize the expression considering operators and immediate values
                    tokens = []
                    operators = []
                    temp_str = ""

                    i = 0
                    while i < len(expression):
                        if expression[i] in op_map or expression[i:i+2] in op_map:  # Check for two-char operators
                            if temp_str:
                                tokens.append(temp_str.strip())
                                temp_str = ""
                            if expression[i:i+2] in op_map:  # Two-char operator
                                operators.append(expression[i:i+2])
                                i += 2
                            else:  # Single-char operator
                                operators.append(expression[i])
                                i += 1
                        else:
                            temp_str += expression[i]
                            i += 1
                    if temp_str:
                        tokens.append(temp_str.strip())

                    # Handle multiple consecutive operations (like int a = b + c + d)
                    if len(tokens) > 1:
                        operand1 = tokens[0]
                        reg1 = allocate_register(operand1)
                        mips_code.append(f"    lw {reg1}, {operand1}")

                        for i in range(1, len(tokens)):
                            operator = operators[i - 1] if i - 1 < len(operators) else None
                            operand2 = tokens[i]

                            # If the next operand is a number or another variable
                            if operand2.isdigit():
                                if operator in immediate_op_map:
                                    mips_code.append(f"    {immediate_op_map[operator]} {reg1}, {reg1}, {operand2}")
                                else:
                                    mips_code.append(f"    {op_map[operator]} {reg1}, {reg1}, {operand2}")
                            else:
                                reg2 = allocate_register(operand2)
                                mips_code.append(f"    lw {reg2}, {operand2}")
                                mips_code.append(f"    {op_map[operator]} {reg1}, {reg1}, {reg2}")

                        # Store the result back to memory
                        mips_code.append(f"    sw {reg1}, {left_var}")
                    else:
                        # Single operand assignment
                        operand = tokens[0]
                        reg = allocate_register(operand)
                        mips_code.append(f"    lw {reg}, {operand}")
                        mips_code.append(f"    sw {reg}, {left_var}")

            if 'else' not in line and 'if' not in line and end_label:
                mips_code.append(f"{end_label}:")  # End label after else branch

    return '\n'.join(mips_code)