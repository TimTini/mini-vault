import tempfile
import unittest
from pathlib import Path
import exporter


class OutputOwnership(unittest.TestCase):
    def test_second_writer_is_rejected_and_lock_is_released(self):
        self.assertTrue(hasattr(exporter,'exclusive_file'),'missing output ownership guard')
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'output.lock'
            with exporter.exclusive_file(path):
                with self.assertRaises(RuntimeError):
                    with exporter.exclusive_file(path):
                        self.fail('second writer entered critical section')
            self.assertFalse(path.exists())


if __name__=='__main__':
    unittest.main()
