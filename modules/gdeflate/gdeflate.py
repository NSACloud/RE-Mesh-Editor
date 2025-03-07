import ctypes
from ctypes import c_bool, c_uint8, c_uint32, c_uint64, POINTER, byref
from pathlib import Path
from typing import Union, Optional
from enum import IntEnum
import platform

class GDeflateCompressionLevel(IntEnum):
    """
    GDeflate compression levels that map to DirectStorage compression levels.
    """
    FASTEST = 1     # Maps to DSTORAGE_COMPRESSION_FASTEST
    DEFAULT = 9     # Maps to DSTORAGE_COMPRESSION_DEFAULT
    BEST_RATIO = 12 # Maps to DSTORAGE_COMPRESSION_BEST_RATIO

class GDeflateFlags (IntEnum):
    """
    GDeflate compression flags
    """
    COMPRESS_SINGLE_THREAD = 0x200

class GDeflateError(Exception):
    """Custom exception for GDeflate-related errors"""
    pass


def is_windows():
    return platform.system() == 'Windows'


def is_linux():
    return platform.system() == 'Linux'


def is_mac():
    return platform.system() == 'Darwin'

class GDeflate:
    """
    A python interface for the GDeflate wrapper library.
    
    Args:
        dll_path (Union[str, Path], optional): Path to the GDeflate DLL. 
            Defaults to "GDeflateWrapper-x86_64.dll" in the current directory.
    
    Raises:
        GDeflateError: If the DLL cannot be loaded or if compression/decompression fails
    """
    
    # Expose compression levels as class attributes
    FASTEST = GDeflateCompressionLevel.FASTEST
    DEFAULT = GDeflateCompressionLevel.DEFAULT
    BEST_RATIO = GDeflateCompressionLevel.BEST_RATIO
    
    def __init__(self, dll_path: Union[str, Path] = None):
        if dll_path is None:
            # Try to find the DLL next to the .py file first
            module_dir = Path(__file__).parent.absolute()
			
            if is_windows():
                dll_name = "GDeflateWrapper.dll"
            elif is_linux():
                dll_name = "libGDeflateWrapper.so"
			#elif is_mac():
				#Maybe TODO
            else:
                raise RuntimeError(f'This OS ({platform.system()}) is unsupported.')
            possible_paths = [
                module_dir / dll_name,           # Next to .py file
                Path.cwd() / dll_name,           # Current working directory
                dll_name,                        # System PATH
            ]
            
            for path in possible_paths:
                try:
                    self._dll = ctypes.CDLL(str(path))
                    break
                except OSError:
                    continue
            else:
                raise GDeflateError(
                    f"Could not find {dll_name} in any of these locations:\n" + 
                    "\n".join(f"- {p}" for p in possible_paths)
                )
        else:
            try:
                self._dll = ctypes.CDLL(str(dll_path))
            except OSError as e:
                raise GDeflateError(f"Failed to load GDeflate DLL from {dll_path}: {e}")
        
        # bool gdeflate_get_uncompressed_size(
        #     uint8_t* input,
        #     uint64_t input_size,
        #     uint64_t* uncompressed_size);
        self._get_uncompressed_size_func = self._dll.gdeflate_get_uncompressed_size
        self._get_uncompressed_size_func.argtypes = [
            POINTER(c_uint8),  # input
            c_uint64,          # input_size
            POINTER(c_uint64)  # uncompressed_size
        ]
        self._get_uncompressed_size_func.restype = c_bool

        # uint64_t gdeflate_get_compress_bound(uint64_t size)
        self._get_compress_bound = self._dll.gdeflate_get_compress_bound
        self._get_compress_bound.argtypes = [
            c_uint64,          # input_size
        ]
        self._get_compress_bound.restype = c_uint64

        # bool gdeflate_decompress(
        #     uint8_t* output,
        #     uint64_t output_size,
        #     uint8_t* input,
        #     uint64_t input_size,
        #     uint32_t num_workers);
        self._decompress_func = self._dll.gdeflate_decompress
        self._decompress_func.argtypes = [
            POINTER(c_uint8),  # output
            c_uint64,          # output_size
            POINTER(c_uint8),  # input
            c_uint64,          # input_size
            c_uint32           # num_workers
        ]
        self._decompress_func.restype = c_bool

        # bool gdeflate_compress(
        #     uint8_t* output,
        #     uint64_t* output_size,
        #     uint8_t* input,
        #     uint64_t input_size,
        #     uint32_t level,
        #     uint32_t flags);
        self._compress_func = self._dll.gdeflate_compress
        self._compress_func.argtypes = [
            POINTER(c_uint8),  # output
            POINTER(c_uint64), # output_size
            POINTER(c_uint8),  # input
            c_uint64,          # input_size
            c_uint32,          # level
            c_uint32           # flags
        ]
        self._compress_func.restype = c_bool
    
    def get_uncompressed_size(self, compressed_data: Union[bytes, bytearray]) -> int:
        """
        Get the uncompressed size of compressed data.
        
        Args:
            compressed_data: The compressed data as bytes or bytearray
            
        Returns:
            int: The size of the data when uncompressed
            
        Raises:
            GDeflateError: If the size calculation fails
        """
        input_array = (c_uint8 * len(compressed_data))(*compressed_data)
        uncompressed_size = c_uint64(0)
        
        success = self._get_uncompressed_size_func(
            input_array,
            c_uint64(len(compressed_data)),
            byref(uncompressed_size)
        )
        
        if not success:
            raise GDeflateError("Failed to get uncompressed size")
        
        return uncompressed_size.value
    
    def decompress(self, 
                  compressed_data: Union[bytes, bytearray], 
                  num_workers: int = 1) -> bytes:
        """
        Decompress GDeflate-compressed data.
        
        Args:
            compressed_data: The compressed data as bytes or bytearray
            num_workers: Number of worker threads to use (default: 1)
            
        Returns:
            bytes: The decompressed data
            
        Raises:
            GDeflateError: If decompression fails
        """
        # Get the uncompressed size first
        output_size = self.get_uncompressed_size(compressed_data)
        
        # Prepare input and output buffers
        input_array = (c_uint8 * len(compressed_data))(*compressed_data)
        output_array = (c_uint8 * output_size)()
        
        success = self._decompress_func(
            output_array,
            c_uint64(output_size),
            input_array,
            c_uint64(len(compressed_data)),
            c_uint32(num_workers)
        )
        
        if not success:
            raise GDeflateError("Decompression failed")
        
        return bytes(output_array)
    
    def compress(self, 
                data: Union[bytes, bytearray], 
                level: Union[int, GDeflateCompressionLevel] = GDeflateCompressionLevel.DEFAULT, 
                flags: int = 0) -> bytes:
        """
        Compress data using GDeflate.
        
        Args:
            data: The data to compress as bytes or bytearray
            level: Compression level (default: DEFAULT). Use GDeflateCompressionLevel enum or class constants
            flags: Compression flags (default: 0)
            
        Returns:
            bytes: The compressed data
            
        Raises:
            GDeflateError: If compression fails
        """

        # Get size of output buffer to allocate,
        # small inputs _can_ compress to be larger than the input buffer.
        bounded_output_size = self._get_compress_bound(c_uint64(len(data)))

        # Allocate input/output buffers and output size var.
        output_size = c_uint64(bounded_output_size)
        output_array = (c_uint8 * bounded_output_size)()
        input_array = (c_uint8 * len(data))(*data)
        
        success = self._compress_func(
            output_array,
            byref(output_size),
            input_array,
            c_uint64(len(data)),
            c_uint32(int(level)),  # Convert enum to int if needed
            c_uint32(flags)
        )
        
        if not success:
            raise GDeflateError("Compression failed")
        
        # Return only the actual compressed bytes
        return bytes(output_array[:output_size.value])