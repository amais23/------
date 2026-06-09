import os

def patch():
    b64_path = "/Users/Shared/西洋棋代理人/rl_starter_12/scratch/maze_b64.txt"
    model_path = "/Users/Shared/西洋棋代理人/rl_starter_12/model.py"
    
    with open(b64_path, "r") as f:
        b64_str = f.read().strip()
        
    print(f"Read base64 string of length {len(b64_str)} from {b64_path}")
    
    with open(model_path, "r") as f:
        content = f.read()
        
    # Find the start and end of MAZE_1_BASE64 = ( ... )
    start_marker = "MAZE_1_BASE64 = ("
    end_marker = ")"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Error: Could not find MAZE_1_BASE64 start marker in model.py!")
        return
        
    # Find the closing parenthesis after the start_idx
    # We look for the first ')' after the start_idx that is followed by a newline and 'def' or 'SAVE_PATH'
    # Actually, we can just find the closing parenthesis of the tuple.
    # Let's search line by line.
    lines = content.splitlines()
    start_line_idx = -1
    end_line_idx = -1
    
    for i, line in enumerate(lines):
        if "MAZE_1_BASE64 = (" in line:
            start_line_idx = i
        elif start_line_idx != -1 and line.strip() == ")":
            end_line_idx = i
            break
            
    if start_line_idx == -1 or end_line_idx == -1:
        print("Error: Could not locate the MAZE_1_BASE64 block lines!")
        return
        
    # Format the b64_str as chunked lines of 76 characters
    chunk_size = 76
    formatted_chunks = []
    for i in range(0, len(b64_str), chunk_size):
        chunk = b64_str[i:i+chunk_size]
        formatted_chunks.append(f"    \"{chunk}\"")
        
    new_block = [
        "MAZE_1_BASE64 = (",
        *formatted_chunks,
        ")"
    ]
    
    new_lines = lines[:start_line_idx] + new_block + lines[end_line_idx+1:]
    
    with open(model_path, "w") as f:
        f.write("\n".join(new_lines) + "\n")
        
    print(f"Successfully patched {model_path} with {len(formatted_chunks)} lines of base64 data!")

if __name__ == "__main__":
    patch()
