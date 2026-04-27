#ifndef JPEGLS_TB_HPP
#define JPEGLS_TB_HPP

#include <string>
#include <vector>
#include <cstdint>

struct TestCase {
    const char *name;
};

struct ImageDims {
    int height;
    int width;
};

ImageDims read_dims_file(const std::string &path);
std::vector<uint8_t> read_hex_mem_file(const std::string &path);
int read_json_int_field(const std::string &path, const std::string &key);
std::string find_data_dir();
bool file_exists(const std::string &path);

#endif  // JPEGLS_TB_HPP
