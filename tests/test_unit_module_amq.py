import unittest
import mock

from cct.modules.amq.cct_module import AMQ
from cct.errors import CCTError


class TestAMQModule(unittest.TestCase):

    def setUp(self):
        self.amq = AMQ('amq', 'amq')

    @mock.patch('cct.modules.amq.cct_module.add_element')
    def test_should_setup_authentication(self, mock_add_element):
        m = mock.mock_open()
        with mock.patch("__builtin__.open", m, create=True):
            self.amq.setup_authentication('user', 'pass')

        m.assert_called_once_with('users.ini', 'w')
        m().write.assert_called_once_with('user=pass\n')
        mock_add_element.assert_called_once_with(
            'activemq.xml', ".//*[local-name()='broker']/*[local-name()='plugins']", '<jaasAuthenticationPlugin configuration="activemq"/>')

    def test_should_fail_setup_authentication_when_there_is_no_password(self):
        with self.assertRaises(CCTError) as cm:
            self.amq.setup_authentication('user', None)

        self.assertEquals(str(
            cm.exception), 'Username or password not provided, we cannot proceed with setting up AMQ authentication without it')

    def test_should_fail_setup_authentication_if_empty_password_is_provided(self):
        with self.assertRaises(CCTError) as cm:
            self.amq.setup_authentication('user', '')
        self.assertEquals(str(
            cm.exception), 'Username or password not provided, we cannot proceed with setting up AMQ authentication without it')

if __name__ == '__main__':
    unittest.main()
