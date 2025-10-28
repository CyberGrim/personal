import re
import os
from enum import Enum
from pathlib import Path
from textnode import TextNode, TextType, text_node_to_html_node
from htmlnode import LeafNode, ParentNode

class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"

def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        node_parts = node.text.split(delimiter)
        if len(node_parts) % 2 == 0:
            raise Exception("The markdown used has invalid syntax")
        for i, part in enumerate(node_parts):
            current_type = text_type if i % 2 == 1 else TextType.TEXT
            if part:
                new_nodes.append(TextNode(part, current_type, None))

    return new_nodes

def extract_markdown_images(text):
    return re.findall(r'!\[([^\[\]]*)\]\(([^()]*)\)', text)

def extract_markdown_links(text):
    return re.findall(r'(?<!\!)\[(?!\!\[)([^\[\]]*)\]\(([^()]*)\)', text)

def split_nodes_image(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        
        images = extract_markdown_images(node.text)
        if not images:
            new_nodes.append(node)
            continue
        
        text = node.text
        for alt_text, url in images:
            pattern = f"![{alt_text}]({url})"
            if pattern in text:
                parts = text.split(pattern, 1)
                if len(parts) == 2:
                    if parts[0]:
                        new_nodes.append(TextNode(parts[0], TextType.TEXT))
                    new_nodes.append(TextNode(alt_text, TextType.IMAGE, url))
                    text = parts[1]
        
        if text:
            new_nodes.append(TextNode(text, TextType.TEXT))
    
    return new_nodes

def split_nodes_link(old_nodes):
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        
        links = extract_markdown_links(node.text)
        if not links:
            new_nodes.append(node)
            continue
        
        text = node.text
        for link_text, url in links:
            pattern = f"[{link_text}]({url})"
            if pattern in text:
                parts = text.split(pattern, 1)
                if len(parts) == 2:
                    if parts[0]:
                        new_nodes.append(TextNode(parts[0], TextType.TEXT))
                    if link_text:
                        new_nodes.append(TextNode(link_text, TextType.LINK, url))
                    text = parts[1]
        
        if text:
            new_nodes.append(TextNode(text, TextType.TEXT))
    
    return new_nodes

def text_to_textnodes(text):
    first_node = [TextNode(text, TextType.TEXT)]
    code_nodes = split_nodes_delimiter(first_node, "`", TextType.CODE)
    image_nodes = split_nodes_image(code_nodes)
    link_nodes = split_nodes_link(image_nodes)
    bold_nodes = split_nodes_delimiter(link_nodes, "**", TextType.BOLD)
    final_nodes = split_nodes_delimiter(bold_nodes, "_", TextType.ITALIC)

    return final_nodes

def markdown_to_blocks(markdown):
    blocks = markdown.split('\n\n')
    cleaned_blocks = []
    for block in blocks:
        cleaned = block.strip().strip('\n')
        if cleaned == "":
            continue
        cleaned_blocks.append(cleaned)
    return cleaned_blocks

def block_to_block_type(block):
    lines = block.splitlines()

    # Testing for Headings
    i = 0
    while i < len(block) and block[i] == '#':
        i += 1
    if 1 <= i <= 6 and len(block) > i and block[i] == ' ' and len(block.strip()) > i:
        return BlockType.HEADING
              
    # Testing for Code
    if len(lines) >= 2 and lines[0].startswith('```') and lines[-1].strip() == '```':
        return BlockType.CODE

    # Testing for Quotes
    if all(line.startswith('>') for line in lines):
        return BlockType.QUOTE

    # Testing for Unordered Lists
    if all(line.startswith('- ') for line in lines):
        return BlockType.UNORDERED_LIST
    
    # Testing for Ordered Lists
    expected = 1
    for line in lines:
        if not line.startswith(f'{expected}. '):
            break
        expected += 1
    if expected == len(lines) + 1:
        return BlockType.ORDERED_LIST
    
    # For anything else, there's Mastercard. Or a Paragraph type
    return BlockType.PARAGRAPH

def markdown_to_html_node(markdown):
    split_blocks = markdown_to_blocks(markdown)
    final_blocks = []

    for block in split_blocks:
        determined_block = block_to_block_type(block)
        if determined_block == BlockType.CODE:
            final_blocks.append(ParentNode("pre", [LeafNode("code", get_code_text(block))]))
        elif determined_block == BlockType.PARAGRAPH:
            final_blocks.append(ParentNode(f"p", text_to_children(" ".join(block.splitlines()))))
        elif determined_block == BlockType.HEADING:
            parsed = parse_heading(block)
            if not parsed:
                continue
            level, text = parsed
            final_blocks.append(ParentNode(f"h{level}", text_to_children(text)))
        elif determined_block == BlockType.CODE:
            final_blocks.append(ParentNode("pre", [LeafNode("code", get_code_text(block))]))
        elif determined_block == BlockType.QUOTE:
            final_blocks.append(ParentNode("blockquote", text_to_children(get_quote_text(block))))
        elif determined_block == BlockType.UNORDERED_LIST:
            final_blocks.append(ParentNode("ul", [ParentNode("li", text_to_children(item)) for item in get_unordered_list_items(block)]))
        elif determined_block == BlockType.ORDERED_LIST:
            final_blocks.append(ParentNode("ol", [ParentNode("li", text_to_children(item)) for item in get_ordered_list_items(block)]))

    return ParentNode("div", final_blocks)

def text_to_children(text):
    return [text_node_to_html_node(n) for n in text_to_textnodes(text)]

def get_quote_text(block):
    return " ".join(line[2:] if line.startswith("> ") else line for line in block.splitlines(keepends=True))
 
def get_code_text(block):
    lines = block.splitlines(keepends=True)
    inner = lines[1:-1]
    return "".join(inner)

def get_unordered_list_items(block):
    return [line[2:] for line in block.splitlines()]

def get_ordered_list_items(block):
    items = []
    for line in block.splitlines():
        idx = line.find(". ")
        items.append(line[idx+2:] if idx != -1 else line)
    return items

def parse_heading(block):
    i = 0
    while i < len(block) and block[i] == '#':
        i += 1
    if 1 <= i <= 6 and len(block) > i and block[i] == ' ' and len(block.strip()) > i:
        start_index = i + 1
        text = block[start_index:].split("\n", 1)[0]
        if text.strip() == "":
            return None
        return (i, text.strip())
    return None

def extract_title(markdown):
    lines = markdown.splitlines()
    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line
            break
    
    if not title:
        raise ValueError ("No title found")
    
    return title.replace("# ", "", 1).strip()

def generate_page(basepath, from_path, template_path, dest_path):
    missing_parts = []
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")

    with open(from_path, "r", encoding="utf-8") as file:
        markdown = file.read()

    with open(template_path, "r", encoding="utf-8") as file:
        template = file.read()

    html = markdown_to_html_node(markdown).to_html()
    try:
        title = extract_title(markdown)
    except ValueError as e:
        raise ValueError(f"Title missing from {from_path}: {e}") from e

    dirpath = os.path.dirname(dest_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    if "{{ Title }}" not in template:
        missing_parts.append("Title")
    if "{{ Content }}" not in template:
        missing_parts.append("Content")
    
    if missing_parts:
        raise ValueError (f"Template is missing components needed for usage: {missing_parts}")

    completed_page = replace_content(template, title, html, basepath)

    with open(dest_path, "w+", encoding="utf-8") as file:
        file.write(completed_page)

def generate_pages_recursive(basepath, content_dir_path, template_path, dest_dir_path):
    markdown_paths = get_markdown_pages(content_dir_path)

    for from_path in markdown_paths:
        dest_path = Path(from_path.replace(content_dir_path, dest_dir_path)).with_suffix(".html")
        generate_page(basepath, from_path, template_path, dest_path)

def get_markdown_pages(content_path):
    markdown_paths = []
    
    for item in os.listdir(content_path):
        child_src = os.path.join(content_path, item)

        if os.path.isdir(child_src):
            child_path = get_markdown_pages(child_src)
            if child_path:
                markdown_paths += child_path
        else:
            if child_src.endswith(".md"):
                markdown_paths.append(child_src)

    return markdown_paths

def replace_content(template, title, html, basepath):
    # Replace Title
    returning_page = template.replace("{{ Title }}", title)
    # Replace Body
    returning_page = returning_page.replace("{{ Content }}", html)
    # Replace href's
    returning_page = returning_page.replace('href="/', f'href="{basepath}')
    # Replace src's
    returning_page = returning_page.replace('src="/', f'src="{basepath}')

    return returning_page