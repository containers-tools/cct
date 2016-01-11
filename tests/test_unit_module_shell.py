import unittest
import mock

from cct.modules.base.shell import Shell
from cct.errors import CCTError

class TestShellModule(unittest.TestCase):
    def setUp(self):
        self.shell = Shell('shell', 'shell')

    def test_with_single_arg(self):
        self.shell.shell('ls')

    def test_with_multiple_args(self):
        self.shell.shell('ls -l')

    def test_should_raise_if_command_fails(self):
        with self.assertRaises(CCTError) as cm:
            self.shell.shell('doesnt exist')

        ex = cm.exception

        self.assertEqual(str(ex), "Command 'doesnt exist' failed")

if __name__ == '__main__':
    unittest.main()
