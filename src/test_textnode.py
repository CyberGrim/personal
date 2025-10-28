import unittest

from src.textnode import TextNode, TextType, text_node_to_html_node


class TestTextNode(unittest.TestCase):
    """Test cases for TextNode class equality and basic functionality."""
    
    def test_eq(self):
        """Test that two TextNodes with same attributes are equal."""
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a text node", TextType.BOLD)
        self.assertEqual(node, node2)

    def test_not_eq_different_type(self):
        """Test that TextNodes with different text types are not equal."""
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a text node", TextType.ITALIC)
        self.assertNotEqual(node, node2)

    def test_not_eq_different_text(self):
        """Test that TextNodes with different text content are not equal."""
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("Different text", TextType.BOLD)
        self.assertNotEqual(node, node2)

    def test_not_eq_different_url(self):
        """Test that TextNodes with different URLs are not equal."""
        node = TextNode("Link text", TextType.LINK, "https://example.com")
        node2 = TextNode("Link text", TextType.LINK, "https://different.com")
        self.assertNotEqual(node, node2)

    def test_url_none_equality(self):
        """Test that TextNodes with None URL are equal to those without URL."""
        node = TextNode("This is a text node", TextType.BOLD, None)
        node2 = TextNode("This is a text node", TextType.BOLD)
        self.assertEqual(node, node2)

    def test_repr(self):
        """Test that TextNode representation is correct."""
        node = TextNode("Test text", TextType.CODE, "https://example.com")
        expected = "TextNode(Test text, code, https://example.com)"
        self.assertEqual(repr(node), expected)


class TestTextNodeToHtmlNode(unittest.TestCase):
    """Test cases for text_node_to_html_node conversion function."""
    
    def test_text_conversion(self):
        """Test conversion of plain text node to HTML."""
        node = TextNode("Hello, world!", TextType.TEXT)
        html_node = text_node_to_html_node(node)
        self.assertIsNone(html_node.tag)
        self.assertEqual(html_node.value, "Hello, world!")
        self.assertEqual(html_node.props, {})

    def test_bold_conversion(self):
        """Test conversion of bold text node to HTML."""
        node = TextNode("Bold text", TextType.BOLD)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "b")
        self.assertEqual(html_node.value, "Bold text")
        self.assertEqual(html_node.props, {})

    def test_italic_conversion(self):
        """Test conversion of italic text node to HTML."""
        node = TextNode("Italic text", TextType.ITALIC)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "i")
        self.assertEqual(html_node.value, "Italic text")
        self.assertEqual(html_node.props, {})

    def test_code_conversion(self):
        """Test conversion of code text node to HTML."""
        node = TextNode("def hello(): pass", TextType.CODE)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "code")
        self.assertEqual(html_node.value, "def hello(): pass")
        self.assertEqual(html_node.props, {})

    def test_link_conversion(self):
        """Test conversion of link text node to HTML."""
        node = TextNode("Click me", TextType.LINK, "https://www.example.com")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "a")
        self.assertEqual(html_node.value, "Click me")
        self.assertEqual(html_node.props, {"href": "https://www.example.com"})

    def test_image_conversion(self):
        """Test conversion of image text node to HTML."""
        node = TextNode("Alt text", TextType.IMAGE, "image.png")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "img")
        self.assertEqual(html_node.value, "")
        self.assertEqual(html_node.props, {"src": "image.png", "alt": "Alt text"})

    def test_empty_text_conversion(self):
        """Test conversion of empty text node."""
        node = TextNode("", TextType.TEXT)
        html_node = text_node_to_html_node(node)
        self.assertIsNone(html_node.tag)
        self.assertEqual(html_node.value, "")
        self.assertEqual(html_node.props, {})

    def test_special_characters_conversion(self):
        """Test conversion of text with special characters."""
        node = TextNode("Text with <>&\"'", TextType.BOLD)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "b")
        self.assertEqual(html_node.value, "Text with <>&\"'")
        self.assertEqual(html_node.props, {})

    def test_long_text_conversion(self):
        """Test conversion of long text content."""
        long_text = "This is a very long text that might be used to test edge cases in the conversion process. " * 10
        node = TextNode(long_text, TextType.CODE)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "code")
        self.assertEqual(html_node.value, long_text)
        self.assertEqual(html_node.props, {})

    def test_link_with_special_url(self):
        """Test link conversion with special characters in URL."""
        node = TextNode("Special link", TextType.LINK, "https://example.com/path?param=value&other=123")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "a")
        self.assertEqual(html_node.value, "Special link")
        self.assertEqual(html_node.props, {"href": "https://example.com/path?param=value&other=123"})

    def test_image_with_special_alt(self):
        """Test image conversion with special characters in alt text."""
        node = TextNode("Image with <>&\"'", TextType.IMAGE, "special-image.png")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "img")
        self.assertEqual(html_node.value, "")
        self.assertEqual(html_node.props, {"src": "special-image.png", "alt": "Image with <>&\"'"})

    def test_invalid_type_conversion(self):
        """Test that invalid text type raises an exception."""
        node = TextNode("Invalid", "invalid_type")
        with self.assertRaises(Exception) as context:
            text_node_to_html_node(node)
        self.assertIn("Text Type requested not permitted", str(context.exception))


if __name__ == "__main__":
    unittest.main()