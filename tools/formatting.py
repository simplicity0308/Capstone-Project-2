# Function to create a display version with the first N lines
def get_first_n_lines(tool_result, n=4):

    # Split the string into lines (assuming each line is separated by a newline character)
    lines = tool_result.split('\n')

    # Only return the first n lines, and append a truncation message if necessary
    truncated_lines = lines[:n]

    # Join the lines back into a string and return
    return '\n'.join(truncated_lines)