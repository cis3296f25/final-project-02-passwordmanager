import unittest
import math
from unittest.mock import patch
from passwordmanager.utils.apiPasswordStrength import get_password_strength


class TestApiPasswordStrength(unittest.TestCase):
    
    def test_empty_password(self):
        """Test that empty password returns 'weak'"""
        self.assertEqual(get_password_strength(""), "weak")
    
    def test_no_valid_characters(self):
        """Test password with no valid character sets returns 'weak'"""
        # Using only spaces or other non-alphanumeric characters not in shift+number set
        self.assertEqual(get_password_strength("   "), "weak")
        self.assertEqual(get_password_strength("\t\n"), "weak")
    
    def test_only_lowercase(self):
        """Test password with only lowercase letters"""
        # Short password with only lowercase should be weak
        # entropy = 5 * log2(26) ≈ 5 * 4.7 ≈ 23.5 -> weak
        self.assertEqual(get_password_strength("abcde"), "weak")
        
        # Medium length password
        # entropy = 10 * log2(26) ≈ 47 -> medium
        self.assertEqual(get_password_strength("abcdefghij"), "medium")
        
        # Long password for strong
        # entropy = 18 * log2(26) ≈ 84.6 -> strong
        self.assertEqual(get_password_strength("abcdefghijklmnopqr"), "strong")
    
    def test_only_uppercase(self):
        """Test password with only uppercase letters"""
        # Same entropy calculations as lowercase
        self.assertEqual(get_password_strength("ABCDE"), "weak")
        self.assertEqual(get_password_strength("ABCDEFGHIJ"), "medium")
        self.assertEqual(get_password_strength("ABCDEFGHIJKLMNOPQR"), "strong")
    
    def test_only_numbers(self):
        """Test password with only numbers"""
        # entropy = 5 * log2(10) ≈ 5 * 3.32 ≈ 16.6 -> weak
        self.assertEqual(get_password_strength("12345"), "weak")
        
        # entropy = 15 * log2(10) ≈ 49.8 -> medium
        self.assertEqual(get_password_strength("123456789012345"), "medium")
        
        # entropy = 25 * log2(10) ≈ 83 -> strong
        self.assertEqual(get_password_strength("1234567890123456789012345"), "strong")
    
    def test_only_shift_numbers(self):
        """Test password with only shift+number keys"""
        # entropy = 5 * log2(10) ≈ 16.6 -> weak
        self.assertEqual(get_password_strength("!@#$%"), "weak")
        
        # entropy = 15 * log2(10) ≈ 49.8 -> medium
        self.assertEqual(get_password_strength("!@#$%^&*()!@#$%"), "medium")
        
        # entropy = 25 * log2(10) ≈ 83 -> strong
        self.assertEqual(get_password_strength("!@#$%^&*()!@#$%^&*()!@#$%^"), "strong")
    
    def test_only_other_symbols(self):
        """Test password with only other symbols"""
        # entropy = 5 * log2(20) ≈ 5 * 4.32 ≈ 21.6 -> weak
        self.assertEqual(get_password_strength("[]{}|"), "weak")
        
        # entropy = 10 * log2(20) ≈ 43.2 -> medium
        self.assertEqual(get_password_strength("[]{}|[]{}|"), "medium")
        
        # entropy = 20 * log2(20) ≈ 86.4 -> strong
        self.assertEqual(get_password_strength("[]{}|[]{}|[]{}|[]{}|"), "strong")
    
    def test_lowercase_and_uppercase(self):
        """Test password with lowercase and uppercase"""
        # charSetSize = 52, log2(52) ≈ 5.7
        # entropy = 8 * log2(52) ≈ 45.6 -> medium
        self.assertEqual(get_password_strength("AbCdEfGh"), "medium")
        
        # entropy = 15 * log2(52) ≈ 85.5 -> strong
        self.assertEqual(get_password_strength("AbCdEfGhIjKlMnO"), "strong")
    
    def test_lowercase_uppercase_numbers(self):
        """Test password with lowercase, uppercase, and numbers"""
        # charSetSize = 62, log2(62) ≈ 5.95
        # entropy = 7 * log2(62) ≈ 41.65 -> medium
        self.assertEqual(get_password_strength("AbC1234"), "medium")
        
        # entropy = 14 * log2(62) ≈ 83.36 -> strong
        # Must include numbers in the password
        self.assertEqual(get_password_strength("AbCdEfGhIjKlMn1"), "strong")
    
    def test_all_character_types(self):
        """Test password with all character types"""
        # charSetSize = 92 (26+26+10+10+20), log2(92) ≈ 6.52
        # entropy = 7 * log2(92) ≈ 45.64 -> medium
        self.assertEqual(get_password_strength("AbC123!@#"), "medium")
        
        # entropy = 13 * log2(92) ≈ 84.81 -> strong
        # Must include lowercase, uppercase, numbers, shift+numbers, and other symbols
        self.assertEqual(get_password_strength("AbCdEfGhIjKlMn1!@#[]"), "strong")
    
    def test_weak_boundary(self):
        """Test passwords at the weak/medium boundary"""
        # entropy = 40 exactly should be weak (entropy > 40 for medium)
        # For charSetSize = 26, length = 40 / log2(26) ≈ 8.5
        # So length 8 should be weak, length 9 should be medium
        self.assertEqual(get_password_strength("abcdefgh"), "weak")
        self.assertEqual(get_password_strength("abcdefghi"), "medium")
    
    def test_medium_boundary(self):
        """Test passwords at the medium/strong boundary"""
        # entropy = 80 exactly should be strong (entropy >= 80)
        # For charSetSize = 26, length = 80 / log2(26) ≈ 17.02
        # 17 chars gives entropy ≈ 79.9 (< 80), so need 18 chars
        self.assertEqual(get_password_strength("abcdefghijklmnopqr"), "strong")
        
        # For charSetSize = 52, length = 80 / log2(52) ≈ 14.03
        # 14 chars gives entropy ≈ 79.8 (< 80), so need 15 chars
        self.assertEqual(get_password_strength("AbCdEfGhIjKlMnO"), "strong")
    
    def test_other_symbols_detection(self):
        """Test that other symbols are properly detected"""
        # Password with other symbols (not shift+number keys)
        # Should add 20 to charSetSize
        self.assertEqual(get_password_strength("a[]"), "weak")
        self.assertEqual(get_password_strength("abcdefghijkl[]"), "medium")
    
    def test_mixed_character_sets(self):
        """Test various combinations of character sets"""
        # Lowercase + numbers (charSetSize = 36, log2(36) ≈ 5.17)
        self.assertEqual(get_password_strength("abc123"), "weak")
        # 16 chars: entropy = 16 * log2(36) ≈ 82.7 -> strong
        self.assertEqual(get_password_strength("abcdefghij123456"), "strong")
        
        # Uppercase + shift+number keys (charSetSize = 36, log2(36) ≈ 5.17)
        self.assertEqual(get_password_strength("ABC!@#"), "weak")
        # 20 chars: entropy = 20 * log2(36) ≈ 103.4 -> strong
        self.assertEqual(get_password_strength("ABCDEFGHIJ!@#$%^&*()"), "strong")
        
        # Numbers + shift+number keys (same set size as just numbers, charSetSize = 10)
        self.assertEqual(get_password_strength("123!@#"), "weak")
        
        # Lowercase + other symbols (charSetSize = 46, log2(46) ≈ 5.52)
        self.assertEqual(get_password_strength("abc[]"), "weak")
        # 18 chars: entropy = 18 * log2(46) ≈ 99.4 -> strong
        self.assertEqual(get_password_strength("abcdefghijklmn[]{}"), "strong")