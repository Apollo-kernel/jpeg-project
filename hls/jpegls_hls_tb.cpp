#include "jpegls_hls.hpp"
#include "jpegls_tb.hpp"

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>

#ifdef JPEGLS_TB_SMALL_ONLY
static const TestCase TESTS[] = {
    {"all_zero_8x8"},
    {"constant_128_8x8"},
    {"horizontal_gradient_8x8"},
    {"vertical_gradient_8x8"},
    {"checkerboard_8x8"},
    {"random_8x8"},
};
#else
static const TestCase TESTS[] = {
    {"all_zero_8x8"},
    {"constant_128_8x8"},
    {"horizontal_gradient_8x8"},
    {"vertical_gradient_8x8"},
    {"checkerboard_8x8"},
    {"random_8x8"},
    {"two_macaws"},
    {"whitewater_rafting"},
};
#endif

bool file_exists(const std::string &path) {
    std::ifstream f(path.c_str(), std::ios::binary);
    return f.good();
}

std::string find_data_dir() {
    const char *candidates[] = {
        "data",
        "../data",
        "../../data",
        "../../../data",
        "../../../../data"
    };

    for (unsigned i = 0; i < sizeof(candidates) / sizeof(candidates[0]); ++i) {
        std::string probe = std::string(candidates[i]) + "/python_results.csv";
        if (file_exists(probe)) {
            return std::string(candidates[i]);
        }
    }

    // Fallback for Vitis HLS runs where files are added as testbench files.
    return "data";
}

ImageDims read_dims_file(const std::string &path) {
    std::ifstream f(path.c_str());
    if (!f) {
        std::cerr << "ERROR: cannot open dims file: " << path << std::endl;
        std::exit(2);
    }

    ImageDims dims;
    f >> dims.height >> dims.width;
    if (!f || dims.height <= 0 || dims.width <= 0) {
        std::cerr << "ERROR: invalid dims in " << path << std::endl;
        std::exit(2);
    }
    return dims;
}

std::vector<uint8_t> read_hex_mem_file(const std::string &path) {
    std::ifstream f(path.c_str());
    if (!f) {
        std::cerr << "ERROR: cannot open mem file: " << path << std::endl;
        std::exit(2);
    }

    std::vector<uint8_t> data;
    std::string line;
    while (std::getline(f, line)) {
        // Trim comments and whitespace.
        std::size_t comment_pos = line.find("//");
        if (comment_pos != std::string::npos) {
            line = line.substr(0, comment_pos);
        }
        comment_pos = line.find("#");
        if (comment_pos != std::string::npos) {
            line = line.substr(0, comment_pos);
        }

        std::stringstream ss(line);
        std::string token;
        while (ss >> token) {
            unsigned value = 0;
            std::stringstream hs;
            hs << std::hex << token;
            hs >> value;
            if (value > 255) {
                std::cerr << "ERROR: byte out of range in " << path << ": " << token << std::endl;
                std::exit(2);
            }
            data.push_back(static_cast<uint8_t>(value));
        }
    }

    return data;
}

int read_json_int_field(const std::string &path, const std::string &key) {
    std::ifstream f(path.c_str());
    if (!f) {
        std::cerr << "ERROR: cannot open json file: " << path << std::endl;
        std::exit(2);
    }

    std::stringstream buffer;
    buffer << f.rdbuf();
    std::string text = buffer.str();

    const std::string quoted_key = "\"" + key + "\"";
    std::size_t p = text.find(quoted_key);
    if (p == std::string::npos) {
        std::cerr << "ERROR: key not found in json: " << key << " file=" << path << std::endl;
        std::exit(2);
    }

    p = text.find(":", p);
    if (p == std::string::npos) {
        std::cerr << "ERROR: malformed json for key: " << key << std::endl;
        std::exit(2);
    }
    p++;

    while (p < text.size() && (text[p] == ' ' || text[p] == '\n' || text[p] == '\r' || text[p] == '\t')) {
        p++;
    }

    bool neg = false;
    if (p < text.size() && text[p] == '-') {
        neg = true;
        p++;
    }

    int value = 0;
    bool any = false;
    while (p < text.size() && text[p] >= '0' && text[p] <= '9') {
        value = value * 10 + (text[p] - '0');
        p++;
        any = true;
    }

    if (!any) {
        std::cerr << "ERROR: integer value not found for key: " << key << std::endl;
        std::exit(2);
    }

    return neg ? -value : value;
}

static bool run_one_case(const std::string &data_dir, const TestCase &tc, std::ofstream &csv) {
    const std::string stem = data_dir + "/" + tc.name;
    const std::string dims_path = stem + "_dims.txt";
    const std::string input_mem_path = stem + ".mem";
    const std::string expected_mem_path = stem + "_compressed.mem";
    const std::string summary_path = stem + "_summary.json";

    const ImageDims dims = read_dims_file(dims_path);
    const std::vector<uint8_t> input = read_hex_mem_file(input_mem_path);
    const std::vector<uint8_t> expected = read_hex_mem_file(expected_mem_path);
    const int expected_nbits = read_json_int_field(summary_path, "valid_bits");

    const int expected_pixels = dims.height * dims.width;
    if ((int)input.size() != expected_pixels) {
        std::cerr << "ERROR: input pixel count mismatch for " << tc.name
                  << " expected=" << expected_pixels
                  << " actual=" << input.size() << std::endl;
        return false;
    }

#ifdef JPEGLS_COSIM_SMALL_DEPTH
    // In C/RTL co-simulation, Vitis wraps m_axi pointers and dumps the full
    // interface depth into transaction files. Therefore the testbench buffers
    // must be at least as large as the HLS interface depth, even when the
    // active test image is only 8x8.
    if ((int)input.size() > JPEGLS_AXI_IN_DEPTH) {
        std::cerr << "ERROR: input exceeds JPEGLS_AXI_IN_DEPTH for " << tc.name << std::endl;
        return false;
    }
    std::vector<pixel_t> in_hls(JPEGLS_AXI_IN_DEPTH);
#else
    std::vector<pixel_t> in_hls(input.size());
#endif

    for (std::size_t i = 0; i < input.size(); ++i) {
        in_hls[i] = input[i];
    }

#ifdef JPEGLS_COSIM_SMALL_DEPTH
    const int max_out_bytes = JPEGLS_AXI_OUT_DEPTH;
    if ((int)expected.size() > max_out_bytes) {
        std::cerr << "ERROR: expected output exceeds JPEGLS_AXI_OUT_DEPTH for " << tc.name << std::endl;
        return false;
    }
#else
    const int max_out_bytes = std::max<int>((int)expected.size() + 4096, (int)input.size() * 16 + 1024);
#endif

    std::vector<byte_t> out_hls(max_out_bytes);
    int out_nbits_mem[1] = {0};
    int status_mem[1] = {0};

    jpegls_encode_hls(
        in_hls.data(),
        out_hls.data(),
        dims.width,
        dims.height,
        max_out_bytes,
        out_nbits_mem,
        status_mem
    );

    const int out_nbits = out_nbits_mem[0];
    const int status = status_mem[0];

    bool pass = true;
    std::string reason = "PASS";

    if (status != 0) {
        pass = false;
        reason = "status=" + std::to_string(status);
    }

    if (out_nbits != expected_nbits) {
        pass = false;
        reason = "nbits mismatch expected=" + std::to_string(expected_nbits) +
                 " actual=" + std::to_string(out_nbits);
    }

    const int actual_bytes = (out_nbits + 7) / 8;
    if (actual_bytes != (int)expected.size()) {
        pass = false;
        reason = "byte count mismatch expected=" + std::to_string(expected.size()) +
                 " actual=" + std::to_string(actual_bytes);
    }

    const int compare_bytes = std::min<int>(actual_bytes, (int)expected.size());
    for (int i = 0; i < compare_bytes; ++i) {
        if ((uint8_t)out_hls[i] != expected[i]) {
            pass = false;
            reason = "byte mismatch at index=" + std::to_string(i) +
                     " expected=" + std::to_string((int)expected[i]) +
                     " actual=" + std::to_string((int)((uint8_t)out_hls[i]));
            break;
        }
    }

    csv << tc.name << ","
        << dims.height << ","
        << dims.width << ","
        << input.size() << ","
        << expected.size() << ","
        << expected_nbits << ","
        << out_nbits << ","
        << (pass ? "PASS" : "FAIL") << ","
        << reason << "\n";

    if (!pass) {
        std::cerr << "FAIL " << tc.name << ": " << reason << std::endl;
    } else {
        std::cout << "PASS " << tc.name << std::endl;
    }

    return pass;
}

int main() {
    const std::string data_dir = find_data_dir();
    std::cout << "Using data directory: " << data_dir << std::endl;

#ifdef JPEGLS_TB_SMALL_ONLY
    const std::string csv_name = "hls_cosim_small_results.csv";
#else
    const std::string csv_name = "hls_csim_results.csv";
#endif

    std::ofstream csv((data_dir + "/" + csv_name).c_str());
    csv << "test_name,height,width,input_bytes,expected_compressed_bytes,expected_nbits,actual_nbits,result,reason\n";

    bool all_pass = true;
    for (unsigned i = 0; i < sizeof(TESTS) / sizeof(TESTS[0]); ++i) {
        const bool pass = run_one_case(data_dir, TESTS[i], csv);
        all_pass = all_pass && pass;
    }

    csv.close();

    if (all_pass) {
        std::cout << "All HLS C simulation tests PASS." << std::endl;
        return 0;
    }

    std::cerr << "One or more HLS C simulation tests FAILED." << std::endl;
    return 1;
}
