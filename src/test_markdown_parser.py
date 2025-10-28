import unittest
from textnode import TextNode, TextType
from markdown_parser import (
    BlockType,
    split_nodes_delimiter, 
    extract_markdown_images, 
    extract_markdown_links,
    split_nodes_image,
    split_nodes_link,
    text_to_textnodes,
    markdown_to_blocks,
    block_to_block_type,
    markdown_to_html_node,
    extract_title
)


class TestSplitNodesDelimiter(unittest.TestCase):
    """Test cases for split_nodes_delimiter function."""
    
    def test_empty_input(self):
        """Test empty input list."""
        new_nodes = split_nodes_delimiter([], "`", TextType.CODE)
        self.assertEqual(len(new_nodes), 0)
        self.assertEqual(new_nodes, [])

    def test_split_with_delimiters(self):
        """Test basic delimiter splitting."""
        node = TextNode("This is text with a `code block` word", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(len(new_nodes), 3)
        self.assertEqual(new_nodes[0].text, "This is text with a ")
        self.assertEqual(new_nodes[0].text_type, TextType.TEXT)
        self.assertEqual(new_nodes[1].text, "code block")
        self.assertEqual(new_nodes[1].text_type, TextType.CODE)
        self.assertEqual(new_nodes[2].text, " word")
        self.assertEqual(new_nodes[2].text_type, TextType.TEXT)

    def test_no_delimiters(self):
        """Test text without delimiters."""
        node = TextNode("Plain text without delimiters", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(len(new_nodes), 1)
        self.assertEqual(new_nodes[0].text, "Plain text without delimiters")
        self.assertEqual(new_nodes[0].text_type, TextType.TEXT)

    def test_multiple_delimited_sections(self):
        """Test multiple delimited sections."""
        node = TextNode("Start `code1` middle `code2` end", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(len(new_nodes), 5)
        self.assertEqual(new_nodes[0].text, "Start ")
        self.assertEqual(new_nodes[1].text, "code1")
        self.assertEqual(new_nodes[1].text_type, TextType.CODE)
        self.assertEqual(new_nodes[2].text, " middle ")
        self.assertEqual(new_nodes[3].text, "code2")
        self.assertEqual(new_nodes[3].text_type, TextType.CODE)
        self.assertEqual(new_nodes[4].text, " end")

    def test_empty_delimited_section(self):
        """Test empty delimited section."""
        node = TextNode("Before `` after", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(len(new_nodes), 2)
        self.assertEqual(new_nodes[0].text, "Before ")
        self.assertEqual(new_nodes[1].text, " after")

    def test_empty_delimited_content_behavior(self):
        """Test that empty delimited content behavior is consistent."""
        # Code delimiters currently ignore empty content (creates 2 nodes)
        node = TextNode("Before `` after", TextType.TEXT)
        result = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].text, "Before ")
        self.assertEqual(result[1].text, " after")
        
        # This is inconsistent with other delimiters which raise exceptions
        # TODO: Consider making this consistent across all delimiters

    def test_missing_closing_delimiters(self):
        """Test that missing closing delimiters raise exceptions."""
        test_cases = [
            ("Before ** after", "**", TextType.BOLD),
            ("Before __ after", "__", TextType.BOLD),
            ("Before _ after", "_", TextType.ITALIC),
            ("Before ` after", "`", TextType.CODE),
        ]
        
        for text, delimiter, text_type in test_cases:
            with self.subTest(text=text, delimiter=delimiter):
                node = TextNode(text, TextType.TEXT)
                with self.assertRaises(Exception) as context:
                    split_nodes_delimiter([node], delimiter, text_type)
                self.assertTrue("invalid syntax" in str(context.exception).lower())

    def test_preserve_non_text_nodes(self):
        """Test that non-TEXT nodes are preserved."""
        node1 = TextNode("Already code", TextType.CODE)
        node2 = TextNode("Text with `code` block", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node1, node2], "`", TextType.CODE)
        self.assertEqual(len(new_nodes), 4)
        self.assertEqual(new_nodes[0].text, "Already code")
        self.assertEqual(new_nodes[0].text_type, TextType.CODE)
        self.assertEqual(new_nodes[1].text, "Text with ")
        self.assertEqual(new_nodes[2].text, "code")
        self.assertEqual(new_nodes[3].text, " block")

    def test_invalid_delimiter_pairs(self):
        """Test invalid delimiter pairs raise exception."""
        node = TextNode("Text with `unpaired delimiter", TextType.TEXT)
        with self.assertRaises(Exception) as context:
            split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertTrue("invalid syntax" in str(context.exception).lower())

    def test_bold_text(self):
        """Test bold text delimiter."""
        node = TextNode("This is **bold** text", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(len(new_nodes), 3)
        self.assertEqual(new_nodes[0].text, "This is ")
        self.assertEqual(new_nodes[0].text_type, TextType.TEXT)
        self.assertEqual(new_nodes[1].text, "bold")
        self.assertEqual(new_nodes[1].text_type, TextType.BOLD)
        self.assertEqual(new_nodes[2].text, " text")
        self.assertEqual(new_nodes[2].text_type, TextType.TEXT)

    def test_italic_text(self):
        """Test italic text delimiter."""
        node = TextNode("This is _italic_ text", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "_", TextType.ITALIC)
        self.assertEqual(len(new_nodes), 3)
        self.assertEqual(new_nodes[0].text, "This is ")
        self.assertEqual(new_nodes[0].text_type, TextType.TEXT)
        self.assertEqual(new_nodes[1].text, "italic")
        self.assertEqual(new_nodes[1].text_type, TextType.ITALIC)
        self.assertEqual(new_nodes[2].text, " text")
        self.assertEqual(new_nodes[2].text_type, TextType.TEXT)

    def test_mixed_markdown(self):
        """Test mixed markdown processing."""
        node = TextNode("**Bold** and _italic_ and `code`", TextType.TEXT)
        # Test bold first
        bold_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        # Test italic on the result
        italic_nodes = split_nodes_delimiter(bold_nodes, "_", TextType.ITALIC)
        # Finally test code
        final_nodes = split_nodes_delimiter(italic_nodes, "`", TextType.CODE)
        
        self.assertEqual(len(final_nodes), 5)
        expected_types = [TextType.BOLD, TextType.TEXT, TextType.ITALIC, TextType.TEXT, TextType.CODE]
        expected_texts = ["Bold", " and ", "italic", " and ", "code"]
        
        for i, node in enumerate(final_nodes):
            self.assertEqual(node.text_type, expected_types[i])
            self.assertEqual(node.text, expected_texts[i])

    def test_empty_node_list_with_content(self):
        """Test empty node list."""
        nodes = [TextNode("", TextType.TEXT)]
        new_nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
        self.assertEqual(len(new_nodes), 0)


class TestMarkdownExtraction(unittest.TestCase):
    """Test cases for markdown extraction functions."""
    
    def test_extract_markdown_images(self):
        """Test extracting multiple images."""
        matches = extract_markdown_images(
            "This is text with a ![rick roll](https://i.imgur.com/aKaOqIh.gif) and ![obi wan](https://i.imgur.com/fJRm4Vk.jpeg)"
        )
        self.assertEqual(
            matches,
            [
                ("rick roll", "https://i.imgur.com/aKaOqIh.gif"),
                ("obi wan", "https://i.imgur.com/fJRm4Vk.jpeg")
            ]
        )

    def test_single_image(self):
        """Test extracting single image."""
        matches = extract_markdown_images(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)"
        )
        self.assertEqual(
            matches,
            [("image", "https://i.imgur.com/zjjcJKZ.png")]
        )

    def test_extract_markdown_links(self):
        """Test extracting multiple links."""
        text = "This is text with a link [to boot dev](https://www.boot.dev) and [to youtube](https://www.youtube.com/@bootdotdev)"
        self.assertEqual(
            extract_markdown_links(text),
            [
                ("to boot dev", "https://www.boot.dev"),
                ("to youtube", "https://www.youtube.com/@bootdotdev")
            ]
        )

    def test_single_link(self):
        """Test extracting single link."""
        text = "This is a [link](https://boot.dev) in text"
        self.assertEqual(
            extract_markdown_links(text),
            [("link", "https://boot.dev")]
        )

    def test_no_matches(self):
        """Test text with no matches."""
        self.assertEqual(extract_markdown_images("Plain text"), [])
        self.assertEqual(extract_markdown_links("Plain text"), [])

    def test_links_not_matching_images(self):
        """Test that links don't match image patterns."""
        text = "![image](image.jpg) and [link](url)"
        self.assertEqual(extract_markdown_links(text), [("link", "url")])
        
    def test_nested_brackets_safety(self):
        """Test nested brackets are handled correctly."""
        text = "[![img alt](img.jpg)](url)"
        self.assertEqual(extract_markdown_links(text), [])
        self.assertEqual(extract_markdown_images(text), [("img alt", "img.jpg")])

    def test_special_characters_in_alt_text(self):
        """Test special characters in alt text."""
        text = "![alt with <>&\"'](url)"
        matches = extract_markdown_images(text)
        self.assertEqual(matches, [("alt with <>&\"'", "url")])

    def test_special_characters_in_urls(self):
        """Test special characters in URLs."""
        text = "![alt](url?param=value&other=123)"
        matches = extract_markdown_images(text)
        self.assertEqual(matches, [("alt", "url?param=value&other=123")])

    def test_empty_alt_text(self):
        """Test empty alt text."""
        text = "![](url)"
        matches = extract_markdown_images(text)
        self.assertEqual(matches, [("", "url")])

    def test_empty_url(self):
        """Test empty URL."""
        text = "![alt]()"
        matches = extract_markdown_images(text)
        self.assertEqual(matches, [("alt", "")])


class TestSplitNodesImage(unittest.TestCase):
    """Test cases for split_nodes_image function."""
    
    def test_single_image(self):
        """Test single image conversion."""
        node = TextNode("Text ![img](url) more", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("Text ", TextType.TEXT),
            TextNode("img", TextType.IMAGE, "url"),
            TextNode(" more", TextType.TEXT)
        ]
        self.assertEqual(result, expected)

    def test_multiple_images_with_text_between(self):
        """Test multiple images with text between them."""
        node = TextNode("Start ![img1](url1) middle ![img2](url2) end", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("Start ", TextType.TEXT),
            TextNode("img1", TextType.IMAGE, "url1"),
            TextNode(" middle ", TextType.TEXT),
            TextNode("img2", TextType.IMAGE, "url2"),
            TextNode(" end", TextType.TEXT)
        ]
        self.assertEqual(result, expected)

    def test_image_at_start(self):
        """Test image at the very beginning."""
        node = TextNode("![start](start.jpg) some text", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("start", TextType.IMAGE, "start.jpg"),
            TextNode(" some text", TextType.TEXT)
        ]
        self.assertEqual(result, expected)

    def test_image_at_end(self):
        """Test image at the very end."""
        node = TextNode("some text ![end](end.jpg)", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("some text ", TextType.TEXT),
            TextNode("end", TextType.IMAGE, "end.jpg")
        ]
        self.assertEqual(result, expected)

    def test_adjacent_images(self):
        """Test adjacent images with no text between."""
        node = TextNode("![img1](url1)![img2](url2)", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("img1", TextType.IMAGE, "url1"),
            TextNode("img2", TextType.IMAGE, "url2")
        ]
        self.assertEqual(result, expected)

    def test_image_with_no_surrounding_text(self):
        """Test image with no surrounding text."""
        node = TextNode("![only](only.jpg)", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("only", TextType.IMAGE, "only.jpg")
        ]
        self.assertEqual(result, expected)

    def test_no_images_at_all(self):
        """Test text with no images."""
        node = TextNode("Just plain text with no images", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [node]
        self.assertEqual(result, expected)

    def test_duplicate_images(self):
        """Test handling of duplicate image patterns."""
        node = TextNode("First ![same](url) middle ![same](url) last", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("First ", TextType.TEXT),
            TextNode("same", TextType.IMAGE, "url"),
            TextNode(" middle ", TextType.TEXT),
            TextNode("same", TextType.IMAGE, "url"),
            TextNode(" last", TextType.TEXT)
        ]
        self.assertEqual(result, expected)

    def test_non_text_nodes_passed_through(self):
        """Test that non-TEXT nodes are passed through unchanged."""
        node = TextNode("Bold text", TextType.BOLD)
        result = split_nodes_image([node])
        expected = [node]
        self.assertEqual(result, expected)

    def test_empty_text_node(self):
        """Test empty text node."""
        node = TextNode("", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [node]
        self.assertEqual(result, expected)

    def test_special_characters_in_alt_text(self):
        """Test special characters in alt text."""
        node = TextNode("![alt with <>&\"'](url)", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("alt with <>&\"'", TextType.IMAGE, "url")
        ]
        self.assertEqual(result, expected)

    def test_special_characters_in_urls(self):
        """Test special characters in URLs."""
        node = TextNode("![alt](url?param=value&other=123)", TextType.TEXT)
        result = split_nodes_image([node])
        expected = [
            TextNode("alt", TextType.IMAGE, "url?param=value&other=123")
        ]
        self.assertEqual(result, expected)

    def test_no_empty_nodes_created(self):
        """Test that no empty TextNodes are created."""
        test_cases = [
            "![img](url)",  # Only image
            "![img1](url1)![img2](url2)",  # Adjacent images
            "![img](url) text",  # Image at start
            "text ![img](url)",  # Image at end
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                node = TextNode(text, TextType.TEXT)
                result = split_nodes_image([node])
                
                # Check that no empty text nodes are created
                for n in result:
                    if n.text_type == TextType.TEXT:
                        self.assertTrue(len(n.text) > 0, f"Empty TextNode found for text: {text}")

    def test_order_independence(self):
        """Test that processing works regardless of extraction order."""
        text = "![first](url1) middle ![second](url2)"
        node = TextNode(text, TextType.TEXT)
        result = split_nodes_image([node])
        
        # Should process in text order, not extraction order
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].text_type, TextType.IMAGE)
        self.assertEqual(result[0].text, "first")
        self.assertEqual(result[1].text_type, TextType.TEXT)
        self.assertEqual(result[1].text, " middle ")
        self.assertEqual(result[2].text_type, TextType.IMAGE)
        self.assertEqual(result[2].text, "second")

    def test_mixed_content_with_links(self):
        """Test that links are preserved during image processing."""
        text = "Text ![img](img.jpg) with [link](url.com) content"
        node = TextNode(text, TextType.TEXT)
        result = split_nodes_image([node])
        
        # Check that link markdown is preserved in text nodes
        text_nodes = [n for n in result if n.text_type == TextType.TEXT]
        self.assertTrue(any("[link](url.com)" in n.text for n in text_nodes))

    def test_back_to_back_images(self):
        """Test back-to-back image patterns."""
        text = "![img1](url1)![img2](url2)"
        node = TextNode(text, TextType.TEXT)
        result = split_nodes_image([node])
        
        expected = [
            TextNode("img1", TextType.IMAGE, "url1"),
            TextNode("img2", TextType.IMAGE, "url2")
        ]
        self.assertEqual(result, expected)

    def test_back_to_back_links(self):
        """Test back-to-back link patterns."""
        text = "[link1](url1)[link2](url2)"
        node = TextNode(text, TextType.TEXT)
        result = split_nodes_link([node])
        
        expected = [
            TextNode("link1", TextType.LINK, "url1"),
            TextNode("link2", TextType.LINK, "url2")
        ]
        self.assertEqual(result, expected)

    def test_alternating_images_and_links(self):
        """Test alternating image and link patterns."""
        text = "![img1](url1)[link](url)![img2](url2)"
        node = TextNode(text, TextType.TEXT)
        
        # Process images first
        image_result = split_nodes_image([node])
        expected_after_images = [
            TextNode("img1", TextType.IMAGE, "url1"),
            TextNode("[link](url)", TextType.TEXT),
            TextNode("img2", TextType.IMAGE, "url2")
        ]
        self.assertEqual(image_result, expected_after_images)
        
        # Then process links
        link_result = split_nodes_link(image_result)
        expected_final = [
            TextNode("img1", TextType.IMAGE, "url1"),
            TextNode("link", TextType.LINK, "url"),
            TextNode("img2", TextType.IMAGE, "url2")
        ]
        self.assertEqual(link_result, expected_final)

    def test_link_then_image(self):
        """Test link followed by image pattern."""
        text = "[link](url)![img](url)"
        node = TextNode(text, TextType.TEXT)
        
        # Process images first
        image_result = split_nodes_image([node])
        expected_after_images = [
            TextNode("[link](url)", TextType.TEXT),
            TextNode("img", TextType.IMAGE, "url")
        ]
        self.assertEqual(image_result, expected_after_images)
        
        # Then process links
        link_result = split_nodes_link(image_result)
        expected_final = [
            TextNode("link", TextType.LINK, "url"),
            TextNode("img", TextType.IMAGE, "url")
        ]
        self.assertEqual(link_result, expected_final)


class TestSplitNodesLink(unittest.TestCase):
    """Test cases for split_nodes_link function."""
    
    def test_single_link(self):
        """Test single link conversion."""
        node = TextNode("Text [link](url) more", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("Text ", TextType.TEXT),
            TextNode("link", TextType.LINK, "url"),
            TextNode(" more", TextType.TEXT)
        ]
        self.assertEqual(result, expected)

    def test_multiple_links_with_text_between(self):
        """Test multiple links with text between them."""
        node = TextNode("Start [link1](url1) middle [link2](url2) end", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("Start ", TextType.TEXT),
            TextNode("link1", TextType.LINK, "url1"),
            TextNode(" middle ", TextType.TEXT),
            TextNode("link2", TextType.LINK, "url2"),
            TextNode(" end", TextType.TEXT)
        ]
        self.assertEqual(result, expected)

    def test_link_at_start(self):
        """Test link at the very beginning."""
        node = TextNode("[start](start.com) some text", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("start", TextType.LINK, "start.com"),
            TextNode(" some text", TextType.TEXT)
        ]
        self.assertEqual(result, expected)

    def test_link_at_end(self):
        """Test link at the very end."""
        node = TextNode("some text [end](end.com)", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("some text ", TextType.TEXT),
            TextNode("end", TextType.LINK, "end.com")
        ]
        self.assertEqual(result, expected)

    def test_adjacent_links(self):
        """Test adjacent links with no text between."""
        node = TextNode("[link1](url1)[link2](url2)", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("link1", TextType.LINK, "url1"),
            TextNode("link2", TextType.LINK, "url2")
        ]
        self.assertEqual(result, expected)

    def test_link_with_no_surrounding_text(self):
        """Test link with no surrounding text."""
        node = TextNode("[only](only.com)", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("only", TextType.LINK, "only.com")
        ]
        self.assertEqual(result, expected)

    def test_no_links_at_all(self):
        """Test text with no links."""
        node = TextNode("Just plain text with no links", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [node]
        self.assertEqual(result, expected)

    def test_duplicate_links(self):
        """Test handling of duplicate link patterns."""
        node = TextNode("First [same](url) middle [same](url) last", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("First ", TextType.TEXT),
            TextNode("same", TextType.LINK, "url"),
            TextNode(" middle ", TextType.TEXT),
            TextNode("same", TextType.LINK, "url"),
            TextNode(" last", TextType.TEXT)
        ]
        self.assertEqual(result, expected)

    def test_non_text_nodes_passed_through(self):
        """Test that non-TEXT nodes are passed through unchanged."""
        node = TextNode("Bold text", TextType.BOLD)
        result = split_nodes_link([node])
        expected = [node]
        self.assertEqual(result, expected)

    def test_empty_text_node(self):
        """Test empty text node."""
        node = TextNode("", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [node]
        self.assertEqual(result, expected)

    def test_special_characters_in_link_text(self):
        """Test special characters in link text."""
        node = TextNode("[link with <>&\"'](url)", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("link with <>&\"'", TextType.LINK, "url")
        ]
        self.assertEqual(result, expected)

    def test_special_characters_in_urls(self):
        """Test special characters in URLs."""
        node = TextNode("[link](url?param=value&other=123)", TextType.TEXT)
        result = split_nodes_link([node])
        expected = [
            TextNode("link", TextType.LINK, "url?param=value&other=123")
        ]
        self.assertEqual(result, expected)

    def test_no_empty_nodes_created(self):
        """Test that no empty TextNodes are created."""
        test_cases = [
            "[link](url)",  # Only link
            "[link1](url1)[link2](url2)",  # Adjacent links
            "[link](url) text",  # Link at start
            "text [link](url)",  # Link at end
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                node = TextNode(text, TextType.TEXT)
                result = split_nodes_link([node])
                
                # Check that no empty text nodes are created
                for n in result:
                    if n.text_type == TextType.TEXT:
                        self.assertTrue(len(n.text) > 0, f"Empty TextNode found for text: {text}")

    def test_order_independence(self):
        """Test that processing works regardless of extraction order."""
        text = "[first](url1) middle [second](url2)"
        node = TextNode(text, TextType.TEXT)
        result = split_nodes_link([node])
        
        # Should process in text order, not extraction order
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].text_type, TextType.LINK)
        self.assertEqual(result[0].text, "first")
        self.assertEqual(result[1].text_type, TextType.TEXT)
        self.assertEqual(result[1].text, " middle ")
        self.assertEqual(result[2].text_type, TextType.LINK)
        self.assertEqual(result[2].text, "second")


class TestMixedContentProcessing(unittest.TestCase):
    """Test cases for processing mixed content with both images and links."""
    
    def test_mixed_content_processing_order(self):
        """Test that mixed content is processed correctly in sequence."""
        text = "Start ![img](img.jpg) with [link](url.com) and ![img2](img2.jpg) end"
        node = TextNode(text, TextType.TEXT)
        
        # First process images
        image_result = split_nodes_image([node])
        
        # Then process links
        final_result = split_nodes_link(image_result)
        
        # Should have: Start, img, " with ", link, " and ", img2, " end"
        expected_types = [
            TextType.TEXT, TextType.IMAGE, TextType.TEXT, 
            TextType.LINK, TextType.TEXT, TextType.IMAGE, TextType.TEXT
        ]
        actual_types = [n.text_type for n in final_result]
        self.assertEqual(actual_types, expected_types)

    def test_links_untouched_by_image_processing(self):
        """Test that links remain untouched when processing images."""
        text = "Text ![img](img.jpg) with [link](url.com) content"
        node = TextNode(text, TextType.TEXT)
        
        # Process images first
        image_result = split_nodes_image([node])
        
        # Check that link markdown is preserved in text nodes
        text_nodes = [n for n in image_result if n.text_type == TextType.TEXT]
        self.assertTrue(any("[link](url.com)" in n.text for n in text_nodes))
        
        # Process links on the result
        final_result = split_nodes_link(image_result)
        
        # Should have: "Text ", img, " with ", link, " content"
        expected_types = [TextType.TEXT, TextType.IMAGE, TextType.TEXT, TextType.LINK, TextType.TEXT]
        actual_types = [n.text_type for n in final_result]
        self.assertEqual(actual_types, expected_types)

    def test_complex_mixed_content(self):
        """Test complex content with multiple images and links."""
        text = "![img1](url1) text [link1](url1) ![img2](url2) [link2](url2) end"
        node = TextNode(text, TextType.TEXT)
        
        # Process images first
        image_result = split_nodes_image([node])
        
        # Then process links
        final_result = split_nodes_link(image_result)
        
        # Should have: img1, " text ", link1, " ", img2, " ", link2, " end"
        expected_types = [
            TextType.IMAGE, TextType.TEXT, TextType.LINK, 
            TextType.TEXT, TextType.IMAGE, TextType.TEXT, 
            TextType.LINK, TextType.TEXT
        ]
        actual_types = [n.text_type for n in final_result]
        self.assertEqual(actual_types, expected_types)


class TestTextToTextnodes(unittest.TestCase):
    """Test cases for the complete text_to_textnodes pipeline."""
    
    def test_basic_markdown_processing(self):
        """Test basic markdown processing with all features."""
        text = "This is **bold** and _italic_ text with `code` and ![img](url) and [link](url)"
        result = text_to_textnodes(text)
        
        expected_types = [
            TextType.TEXT, TextType.BOLD, TextType.TEXT, TextType.ITALIC, 
            TextType.TEXT, TextType.CODE, TextType.TEXT, TextType.IMAGE, 
            TextType.TEXT, TextType.LINK
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
    
    def test_code_spans_protect_content(self):
        """Test that code spans protect their content from other processing."""
        text = "Text with `code with **bold** and [link](url)` more text"
        result = text_to_textnodes(text)
        
        # Should have: text, code (with protected content), text
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].text_type, TextType.TEXT)
        self.assertEqual(result[1].text_type, TextType.CODE)
        self.assertEqual(result[1].text, "code with **bold** and [link](url)")
        self.assertEqual(result[2].text_type, TextType.TEXT)
    
    def test_processing_order(self):
        """Test that processing order is correct (code first, then images/links, then emphasis)."""
        text = "`code` with ![img](url) and [link](url) and **bold** and _italic_"
        result = text_to_textnodes(text)
        
        # Should process in order: code, images, links, bold, italic
        expected_types = [
            TextType.CODE, TextType.TEXT, TextType.IMAGE, TextType.TEXT, 
            TextType.LINK, TextType.TEXT, TextType.BOLD, TextType.TEXT, TextType.ITALIC
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
    
    def test_empty_alt_text_images(self):
        """Test that empty alt text for images is handled correctly."""
        text = "Text with ![](url) and ![alt](url) and [](url) and [link](url)"
        result = text_to_textnodes(text)
        
        # Should have: text, image (empty alt), text, image (with alt), text, text, link
        expected_types = [
            TextType.TEXT, TextType.IMAGE, TextType.TEXT, TextType.IMAGE, 
            TextType.TEXT, TextType.TEXT, TextType.LINK
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
        
        # Check that empty alt text image was created
        empty_alt_node = result[1]
        self.assertEqual(empty_alt_node.text, "")
        self.assertEqual(empty_alt_node.text_type, TextType.IMAGE)
        self.assertEqual(empty_alt_node.url, "url")
    
    def test_empty_link_text_ignored(self):
        """Test that empty link text is ignored."""
        text = "Text with [](url) and [link](url)"
        result = text_to_textnodes(text)
        
        # Should have: text, text, link (empty link text should be ignored)
        expected_types = [TextType.TEXT, TextType.TEXT, TextType.LINK]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
    
    def test_multiple_emphasis_levels(self):
        """Test multiple levels of emphasis processing."""
        text = "This is **bold** and _italic_ and `code`"
        result = text_to_textnodes(text)
        
        expected_types = [
            TextType.TEXT, TextType.BOLD, TextType.TEXT, TextType.ITALIC, 
            TextType.TEXT, TextType.CODE
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
    
    def test_adjacent_markdown(self):
        """Test adjacent markdown elements."""
        text = "![img](url)[link](url)**bold**_italic_`code`"
        result = text_to_textnodes(text)
        
        expected_types = [
            TextType.IMAGE, TextType.LINK, TextType.BOLD, TextType.ITALIC, TextType.CODE
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
    
    def test_nested_markdown_in_code(self):
        """Test that markdown inside code spans is not processed."""
        text = "Text with `code **bold** and [link](url)` more text"
        result = text_to_textnodes(text)
        
        # Should have: text, code (with unprocessed markdown), text
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1].text_type, TextType.CODE)
        self.assertEqual(result[1].text, "code **bold** and [link](url)")
    
    def test_unmatched_delimiters(self):
        """Test that unmatched delimiters are handled gracefully."""
        text = "Text with single _ underscore and **bold** and single * asterisk"
        
        # This should raise an exception due to unmatched delimiters
        with self.assertRaises(Exception) as context:
            text_to_textnodes(text)
        self.assertTrue("invalid syntax" in str(context.exception).lower())
    
    def test_complex_mixed_content(self):
        """Test complex content with all markdown types."""
        text = "Start with `code` then ![img](url) and [link](url) then **bold** and _italic_ end"
        result = text_to_textnodes(text)
        
        expected_types = [
            TextType.TEXT, TextType.CODE, TextType.TEXT, TextType.IMAGE, 
            TextType.TEXT, TextType.LINK, TextType.TEXT, TextType.BOLD, 
            TextType.TEXT, TextType.ITALIC, TextType.TEXT
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
    
    def test_plain_text(self):
        """Test plain text without any markdown."""
        text = "This is just plain text with no markdown"
        result = text_to_textnodes(text)
        
        # Should return single text node
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text_type, TextType.TEXT)
        self.assertEqual(result[0].text, text)
    
    def test_only_markdown(self):
        """Test text that is only markdown elements."""
        text = "![img](url)[link](url)**bold**_italic_`code`"
        result = text_to_textnodes(text)
        
        expected_types = [
            TextType.IMAGE, TextType.LINK, TextType.BOLD, TextType.ITALIC, TextType.CODE
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
    
    def test_no_empty_nodes_created(self):
        """Test that no empty TextNodes are created."""
        test_cases = [
            "![img](url)[link](url)**bold**_italic_`code`",
            "Text with `code` and **bold**",
            "![img](url) text [link](url)",
            "**bold** and _italic_"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = text_to_textnodes(text)
                
                # Check that no empty text nodes are created
                for node in result:
                    if node.text_type == TextType.TEXT:
                        self.assertTrue(len(node.text) > 0, f"Empty TextNode found for text: {text}")
    
    def test_pipeline_order_preservation(self):
        """Test that the pipeline preserves the order of elements."""
        text = "First ![img](url) second [link](url) third **bold** fourth _italic_ fifth `code`"
        result = text_to_textnodes(text)
        
        # Should preserve order: First, img, second, link, third, bold, fourth, italic, fifth, code
        expected_texts = [
            "First ", "img", " second ", "link", " third ", "bold", 
            " fourth ", "italic", " fifth ", "code"
        ]
        actual_texts = [n.text for n in result]
        self.assertEqual(actual_texts, expected_texts)
    
    def test_special_characters_in_content(self):
        """Test special characters in markdown content."""
        text = "Text with **bold <>&\"'** and _italic <>&\"'_ and `code <>&\"'`"
        result = text_to_textnodes(text)
        
        # Should process all markdown types with special characters
        expected_types = [
            TextType.TEXT, TextType.BOLD, TextType.TEXT, TextType.ITALIC, 
            TextType.TEXT, TextType.CODE
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)
        
        # Check that special characters are preserved
        bold_node = result[1]
        self.assertEqual(bold_node.text, "bold <>&\"'")
        italic_node = result[3]
        self.assertEqual(italic_node.text, "italic <>&\"'")
        code_node = result[5]
        self.assertEqual(code_node.text, "code <>&\"'")

    def test_back_to_back_patterns_in_pipeline(self):
        """Test back-to-back patterns in the full pipeline."""
        text = "![img1](url1)![img2](url2)[link1](url1)[link2](url2)**bold1****bold2**"
        result = text_to_textnodes(text)
        
        expected_types = [
            TextType.IMAGE, TextType.IMAGE, TextType.LINK, TextType.LINK,
            TextType.BOLD, TextType.BOLD
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)

    def test_alternating_patterns_in_pipeline(self):
        """Test alternating patterns in the full pipeline."""
        text = "![img](url)[link](url)![img](url)[link](url)"
        result = text_to_textnodes(text)
        
        expected_types = [
            TextType.IMAGE, TextType.LINK, TextType.IMAGE, TextType.LINK
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)

    def test_complex_alternating_patterns(self):
        """Test complex alternating patterns with all markdown types."""
        text = "![img](url)[link](url)**bold**_italic_`code`![img](url)[link](url)"
        result = text_to_textnodes(text)
        
        expected_types = [
            TextType.IMAGE, TextType.LINK, TextType.BOLD, TextType.ITALIC, 
            TextType.CODE, TextType.IMAGE, TextType.LINK
        ]
        actual_types = [n.text_type for n in result]
        self.assertEqual(actual_types, expected_types)

class TestMarkdownToBlocks(unittest.TestCase):
    def test_markdown_to_blocks(self):
        md = """
This is **bolded** paragraph

This is another paragraph with _italic_ text and `code` here
This is the same paragraph on a new line

- This is a list
- with items
"""
        blocks = markdown_to_blocks(md)
        self.assertEqual(
            blocks,
            [
                "This is **bolded** paragraph",
                "This is another paragraph with _italic_ text and `code` here\nThis is the same paragraph on a new line",
                "- This is a list\n- with items",
            ],
        )

    def test_with_multiple_newlines(self):
        md = "Block 1\n\n\n\nBlock 2"
        blocks = markdown_to_blocks(md)
        self.assertEqual(blocks, ["Block 1", "Block 2"])

    def test_leading_and_trailing_whitespace(self):
        md = "  \n\n  Block 1  \n\n  Block 2  \n\n  "
        blocks = markdown_to_blocks(md)
        self.assertEqual(blocks, ["Block 1", "Block 2"])

    def test_empty_blocks(self):
        md = "Block 1\n\n\n  \n\nBlock 2"
        blocks = markdown_to_blocks(md)
        self.assertEqual(blocks, ["Block 1", "Block 2"])

    def test_single_block(self):
        md = "This is just one block."
        blocks = markdown_to_blocks(md)
        self.assertEqual(blocks, ["This is just one block."])

    def test_empty_input(self):
        md = ""
        blocks = markdown_to_blocks(md)
        self.assertEqual(blocks, [])

    def test_whitespace_input(self):
        md = "   \n\n   \n "
        blocks = markdown_to_blocks(md)
        self.assertEqual(blocks, [])

class TestBlockToBlockType(unittest.TestCase):
    def test_headings(self):
        self.assertEqual(block_to_block_type("# A valid heading"), BlockType.HEADING)
        self.assertEqual(block_to_block_type("###### A valid heading"), BlockType.HEADING)
        self.assertEqual(block_to_block_type("####### Not a heading"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("#NoSpace"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("# "), BlockType.PARAGRAPH)

    def test_code_blocks(self):
        self.assertEqual(block_to_block_type("```\ncode\n```"), BlockType.CODE)
        self.assertEqual(block_to_block_type("```python\ncode\nmore code\n```"), BlockType.CODE)
        self.assertEqual(block_to_block_type("```\n```"), BlockType.CODE, "Code blocks are still created when empty")
        self.assertEqual(block_to_block_type("```code```"), BlockType.PARAGRAPH, "Single-line code is a paragraph")
        self.assertEqual(block_to_block_type("```\ncode"), BlockType.PARAGRAPH, "Missing closing fence")

    def test_quote_blocks(self):
        self.assertEqual(block_to_block_type("> line 1\n> line 2"), BlockType.QUOTE)
        self.assertEqual(block_to_block_type("> just one line"), BlockType.QUOTE)
        self.assertEqual(block_to_block_type("> line 1\nnot a quote"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("> line 1\n>\n> line 3"), BlockType.QUOTE, "Should handle blank lines in quotes")

    def test_unordered_lists(self):
        self.assertEqual(block_to_block_type("- item 1\n- item 2"), BlockType.UNORDERED_LIST)
        self.assertEqual(block_to_block_type("- item 1"), BlockType.UNORDERED_LIST)
        self.assertEqual(block_to_block_type("* item 1"), BlockType.PARAGRAPH, "Should not match * lists")
        self.assertEqual(block_to_block_type("- item 1\nitem 2"), BlockType.PARAGRAPH)

    def test_ordered_lists(self):
        self.assertEqual(block_to_block_type("1. item 1\n2. item 2\n3. item 3"), BlockType.ORDERED_LIST)
        self.assertEqual(block_to_block_type("1. item 1"), BlockType.ORDERED_LIST)
        self.assertEqual(block_to_block_type("1. item 1\n3. item 3"), BlockType.PARAGRAPH, "Should fail on skipped number")
        self.assertEqual(block_to_block_type("2. item 1"), BlockType.PARAGRAPH, "Should fail on wrong start number")
        self.assertEqual(block_to_block_type("1) item 1\n2) item 2"), BlockType.PARAGRAPH, "Should fail on wrong delimiter")

    def test_paragraphs(self):
        self.assertEqual(block_to_block_type("This is a simple paragraph."), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("1. list\n- not a list"), BlockType.PARAGRAPH, "Mixed types should be a paragraph")

class TestBlockToHTML(unittest.TestCase):
    def test_paragraphs(self):
        md = """
This is **bolded** paragraph
text in a p
tag here

This is another paragraph with _italic_ text and `code` here

"""

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><p>This is <b>bolded</b> paragraph text in a p tag here</p><p>This is another paragraph with <i>italic</i> text and <code>code</code> here</p></div>",
        )

    def test_blockquote_simple(self):
        md = """
> This is a _quoted_ line with **inline** `code`
"""
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><blockquote>This is a <i>quoted</i> line with <b>inline</b> <code>code</code></blockquote></div>",
        )

    def test_blockquote_trailing_spaces(self):
        md = """
> This is a _quoted_ line with **inline** `code` and trailing spaces          
"""
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><blockquote>This is a <i>quoted</i> line with <b>inline</b> <code>code</code> and trailing spaces</blockquote></div>",
        )

    def test_blockquote_multiline_two_lines(self):
        md = """
> This is a _quoted_ line with **inline** `code`
> and multiple lines in the same block
"""
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><blockquote>This is a <i>quoted</i> line with <b>inline</b> <code>code</code>\n and multiple lines in the same block</blockquote></div>",
        )

    def test_codeblock(self):
        md = """
```
This is text that _should_ remain
the **same** even with inline stuff
```
"""

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><pre><code>This is text that _should_ remain\nthe **same** even with inline stuff\n</code></pre></div>",
        )

    def test_empty_codeblock(self):
        md = """
```
```
"""
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><pre><code></code></pre></div>",
        )

    def test_heading(self):
        md = """
# This is a heading
"""

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><h1>This is a heading</h1></div>",
        )

    def test_bold_heading(self):
        md = """
# This is a **bold heading**
"""

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><h1>This is a <b>bold heading</b></h1></div>",
        )

    def test_six_hash_heading(self):
        md = """
###### This is a six hash heading
# """

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><h6>This is a six hash heading</h6></div>"
        )

    def test_too_large_heading(self):
        md = """
####### This heading is too large so should be a paragraph
"""

        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><p>####### This heading is too large so should be a paragraph</p></div>"
        )

    def test_heading_inline(self):
        md = "# Hello **world**"
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, "<div><h1>Hello <b>world</b></h1></div>")

    def test_code_ignores_inline(self):
        md = "```\n_not italic_ **bold**\n```"
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, "<div><pre><code>_not italic_ **bold**\n</code></pre></div>")

    def test_paragraph_multiline(self):
        md = "First line\nsecond line"
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, "<div><p>First line second line</p></div>")

    def test_blockquote_multiline(self):
        md = "> first\n> second"
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, "<div><blockquote>first\n second</blockquote></div>")

    def test_unordered_list_inline(self):
        md = "- **bold** item\n- plain"
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, "<div><ul><li><b>bold</b> item</li><li>plain</li></ul></div>")

    def test_large_unordered_list_inline(self):
        md = """- **bold** item
- ![rick roll](https://i.imgur.com/aKaOqIh.gif)
- [link](https://boot.dev)
- _italic_ item 
- plain"""
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, '<div><ul><li><b>bold</b> item</li><li><img src="https://i.imgur.com/aKaOqIh.gif" alt="rick roll"></img></li><li><a href="https://boot.dev">link</a></li><li><i>italic</i> item </li><li>plain</li></ul></div>')

    def test_ordered_list(self):
        md = "1. one\n2. two"
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, "<div><ol><li>one</li><li>two</li></ol></div>")

    def test_large_ordered_list(self):
        md = """1. one (1)
2. two (2)
3. three (3)
4. four (4)
5. five (5)
6. six (6)
7. seven (7)
8. eight (8)
9. nine (9)
10. ten (10)
11. eleven (11)
12. twelve (12)"""
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, "<div><ol><li>one (1)</li><li>two (2)</li><li>three (3)</li><li>four (4)</li><li>five (5)</li><li>six (6)</li><li>seven (7)</li><li>eight (8)</li><li>nine (9)</li><li>ten (10)</li><li>eleven (11)</li><li>twelve (12)</li></ol></div>")

    def test_mixed_document(self):
        md = "# H\n\nPara line 1\nline 2\n\n- a\n- b\n\n```\ncode\n```"
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(
            html,
            "<div><h1>H</h1><p>Para line 1 line 2</p><ul><li>a</li><li>b</li></ul><pre><code>code\n</code></pre></div>",
        )

    def test_ordered_list_weird_numbering(self):
        md = "10. ten\n2. two"
        html = markdown_to_html_node(md).to_html()
        self.assertEqual(html, "<div><p>10. ten 2. two</p></div>")

class TestTitleExtraction(unittest.TestCase):
    def test_title_on_first_line(self):
        md = """# This is a Title
this is some other stuff
and more"""

        result = extract_title(md)
        self.assertEqual(result, "This is a Title")

    def test_title_after_blank_lines(self):
        md = """

# This is a Title after some blank lines
this is some other stuff
and more
"""

        result = extract_title(md)
        self.assertEqual(result, "This is a Title after some blank lines")

    def test_multiple_titles(self):
        md = """
# This is a Title
# This is another one
# This is a third title
"""

        result = extract_title(md)
        self.assertEqual(result, "This is a Title")

    def test_no_title(self):
        md = """
This is a Title (but not really)
this is some other stuff
and more
"""

        with self.assertRaises(ValueError) as context:
            extract_title(md)
        self.assertTrue("no title found" in str(context.exception).lower())

    def test_no_single_hashes(self):
        md = """
## This has headings
### but none of them are singles
### so nothing should return
"""

        with self.assertRaises(ValueError) as context:
            extract_title(md)
        self.assertTrue("no title found" in str(context.exception).lower())

    def test_trailing_hases(self):
        md = """
# C# Basics    
## along with some          random        spaces          
and more
"""

        result = extract_title(md)
        self.assertEqual(result, "C# Basics")

    def test_missing_space(self):
        md = """
#C# Basics    
## along with some          random        spaces          
and more
"""

        with self.assertRaises(ValueError) as context:
            extract_title(md)
        self.assertTrue("no title found" in str(context.exception).lower())

if __name__ == "__main__":
    unittest.main()