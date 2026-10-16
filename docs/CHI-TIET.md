# MINI-VAULT — Danh mục chi tiết có ảnh

Dùng **mã CT + tên chi tiết** dưới đây khi trao đổi hoặc yêu cầu sửa mô hình. Ví dụ: “Tăng độ dày **CT02 – Cánh cửa**”, “Sửa rãnh của **CT21 – Con trượt khóa**”, “Đổi vị trí chốt trên **CT10 – Đĩa mã 2**”. Tên trong dấu `backtick` là giá trị `part` tương ứng trong [mini-vault.scad](../mini-vault.scad).

Danh mục gồm **22 chi tiết**, mỗi mã ứng với một chi tiết trong mô hình. Những chi tiết cùng hình dạng vẫn có mã riêng để chỉ đúng vị trí. Mã CT chỉ dùng trong tài liệu này, không thay tên selector của source.

Ảnh render trực tiếp từ source ngày **16/10/2026**, với tham số **Default** (`size_scale=1`, vỏ 142 × 100 × 84 mm). Mỗi ảnh được phóng vừa khung riêng nên **không dùng kích thước trên ảnh để so tỷ lệ giữa các chi tiết**. Màu chỉ giúp nhìn hình. Hướng ảnh riêng không phải hướng đặt lên bàn in.

Ảnh thu nhỏ **150 px**; bấm vào ảnh để mở bản lớn.

| Mã | Ảnh | Tên chi tiết / selector | Nhận dạng |
| :--- | :---: | :--- | :--- |
| <a id="ct01"></a>**CT01** | <a href="parts/housing.png"><img src="parts/housing.png" alt="CT01 — Vỏ hộp" width="150"></a> | **Vỏ hộp**<br>`housing` | chi tiết lớn dạng hộp rỗng, bốn góc bo tròn; mặt trước mở để lắp cửa. |
| <a id="ct02"></a>**CT02** | <a href="parts/door.png"><img src="parts/door.png" alt="CT02 — Cánh cửa, mặt ngoài" width="150"></a><br><a href="parts/door-inside.png"><img src="parts/door-inside.png" alt="CT02 — Cánh cửa, mặt trong" width="150"></a> | **Cánh cửa**<br>`door` | tấm chữ nhật bo góc, có lỗ tròn cho trục mặt số, lỗ dài cho phần tay kéo của con trượt và vạch chỉ số ở mặt ngoài. |
| <a id="ct03"></a>**CT03** | <a href="parts/hinge_socket_top.png"><img src="parts/hinge_socket_top.png" alt="CT03 — Gối bản lề trên" width="150"></a> | **Gối bản lề trên**<br>`hinge_socket_top` | khối gối nhỏ có vùng nhận trục/chốt bản lề và phần chân/ngàm định vị.. |
| <a id="ct04"></a>**CT04** | <a href="parts/hinge_socket_bottom.png"><img src="parts/hinge_socket_bottom.png" alt="CT04 — Gối bản lề dưới" width="150"></a> | **Gối bản lề dưới**<br>`hinge_socket_bottom` | cùng họ hình học với CT03, được lật đối xứng theo chiều trên/dưới trong source.. |
| <a id="ct05"></a>**CT05** | <a href="parts/hinge_leaf_top.png"><img src="parts/hinge_leaf_top.png" alt="CT05 — Lá bản lề trên" width="150"></a> | **Lá bản lề trên**<br>`hinge_leaf_top` | chi tiết nhỏ có phần thân/ngàm và phần trục nhô để ghép vào gối bản lề.. |
| <a id="ct06"></a>**CT06** | <a href="parts/hinge_leaf_bottom.png"><img src="parts/hinge_leaf_bottom.png" alt="CT06 — Lá bản lề dưới" width="150"></a> | **Lá bản lề dưới**<br>`hinge_leaf_bottom` | bản đối xứng trên/dưới của CT05 trong mô hình.. |
| <a id="ct07"></a>**CT07** | <a href="parts/dial.png"><img src="parts/dial.png" alt="CT07 — Núm xoay mặt số" width="150"></a> | **Núm xoay mặt số**<br>`dial` | đĩa tròn lớn có số/vạch quanh mặt trước, vành cầm quanh chu vi và lỗ ghép trục ở giữa.. |
| <a id="ct08"></a>**CT08** | <a href="parts/shaft.png"><img src="parts/shaft.png" alt="CT08 — Trục mặt số" width="150"></a> | **Trục mặt số**<br>`shaft` | trục dài có đầu tròn dạng bích, đoạn ghép định hình dưới đầu và các đoạn/rãnh giữ ở cuối trục.. |
| <a id="ct09"></a>**CT09** | <a href="parts/disk_1.png"><img src="parts/disk_1.png" alt="CT09 — Đĩa mã 1" width="150"></a> | **Đĩa mã 1**<br>`disk_1` | đĩa tròn mỏng có lỗ tâm lớn, vòng lỗ nhỏ để đặt chốt và một rãnh khuyết ở mép ngoài.. |
| <a id="ct10"></a>**CT10** | <a href="parts/disk_2.png"><img src="parts/disk_2.png" alt="CT10 — Đĩa mã 2" width="150"></a> | **Đĩa mã 2**<br>`disk_2` | cùng hình học cơ bản với CT09, nằm giữa đĩa 1 và đĩa 3 khi lắp.. |
| <a id="ct11"></a>**CT11** | <a href="parts/disk_3.png"><img src="parts/disk_3.png" alt="CT11 — Đĩa mã 3" width="150"></a> | **Đĩa mã 3**<br>`disk_3` | cùng họ đĩa tròn có lỗ và rãnh mép, ở vị trí xa cửa nhất trong cụm ba đĩa.. |
| <a id="ct12"></a>**CT12** | <a href="parts/collar_1.png"><img src="parts/collar_1.png" alt="CT12 — Vòng cổ 1" width="150"></a> | **Vòng cổ 1**<br>`collar_1` | chi tiết vòng có lỗ xuyên tâm, vai tựa và các tai/gờ trên thân; khác đĩa mã ở chỗ không có cả vòng lỗ đặt chốt.. |
| <a id="ct13"></a>**CT13** | <a href="parts/collar_2.png"><img src="parts/collar_2.png" alt="CT13 — Vòng cổ 2" width="150"></a> | **Vòng cổ 2**<br>`collar_2` | cùng hình học cơ bản với CT12, ở tầng giữa của cụm đĩa.. |
| <a id="ct14"></a>**CT14** | <a href="parts/collar_3.png"><img src="parts/collar_3.png" alt="CT14 — Vòng cổ 3" width="150"></a> | **Vòng cổ 3**<br>`collar_3` | cùng họ vòng có vai tựa và tai/gờ, ở tầng xa cửa nhất của ba vòng cổ.. |
| <a id="ct15"></a>**CT15** | <a href="parts/fastener_1.png"><img src="parts/fastener_1.png" alt="CT15 — Chốt đĩa 1" width="150"></a> | **Chốt đĩa 1**<br>`fastener_1` | chốt nhỏ có thân tròn và đầu lớn bo tròn; không có ren vít trong mô hình.. |
| <a id="ct16"></a>**CT16** | <a href="parts/fastener_2.png"><img src="parts/fastener_2.png" alt="CT16 — Chốt đĩa 2" width="150"></a> | **Chốt đĩa 2**<br>`fastener_2` | cùng hình học chốt đầu tròn với CT15.. |
| <a id="ct17"></a>**CT17** | <a href="parts/fastener_3.png"><img src="parts/fastener_3.png" alt="CT17 — Chốt đĩa 3" width="150"></a> | **Chốt đĩa 3**<br>`fastener_3` | cùng họ chốt nhỏ đầu tròn, dành cho đĩa xa cửa.. |
| <a id="ct18"></a>**CT18** | <a href="parts/retaining_ring.png"><img src="parts/retaining_ring.png" alt="CT18 — Vòng chặn trục" width="150"></a> | **Vòng chặn trục**<br>`retaining_ring` | vòng nhỏ có khe hở, khác các vòng cổ có vai/tai đỡ đĩa.. |
| <a id="ct19"></a>**CT19** | <a href="parts/knob.png"><img src="parts/knob.png" alt="CT19 — Núm trong" width="150"></a> | **Núm trong**<br>`knob` | đĩa tròn nhỏ có vành khía để cầm, lỗ tâm định hình và một chốt nhô lệch tâm trên mặt đĩa; không có dãy số như CT07.. |
| <a id="ct20"></a>**CT20** | <a href="parts/link.png"><img src="parts/link.png" alt="CT20 — Thanh liên kết" width="150"></a> | **Thanh liên kết**<br>`link` | thanh dài hẹp, một đầu có phần nhô dạng chữ T, thân có vùng tăng chiều sâu và mặt vát.. |
| <a id="ct21"></a>**CT21** | <a href="parts/latch.png"><img src="parts/latch.png" alt="CT21 — Con trượt khóa" width="150"></a> | **Con trượt khóa**<br>`latch` | chi tiết trượt lớn có thân then, khoang/rãnh dẫn, cổ nối và núm cầm bo tròn liền khối. |
| <a id="ct22"></a>**CT22** | <a href="parts/latch_cover.png"><img src="parts/latch_cover.png" alt="CT22 — Nắp che con trượt" width="150"></a> | **Nắp che con trượt**<br>`latch_cover` | tấm mỏng biên dạng không đều, có ngàm/tai ở mép và cạnh vát; khác cánh cửa lớn CT02.. |

## Quy ước vị trí

- **Mặt ngoài cửa**: phía người sử dụng nhìn thấy núm mặt số và tay kéo khóa.
- **Mặt trong cửa**: phía có cụm ba đĩa mã và cơ cấu gài khóa, hướng vào lòng hộp.
- **Trên/dưới**: theo chiều đứng của hộp trong mô hình lắp, không theo chiều ảnh riêng.
- **Đĩa 1 → 2 → 3**: theo thứ tự trong source, từ gần cánh cửa ra phía trong hộp. Vòng cổ và chốt mang cùng số thuộc vị trí đĩa tương ứng.

Mô tả nhận dạng dựa trên hình học và cách bố trí trong source hiện tại. Mô tả chức năng cơ khí là cách hiểu của mô hình tái dựng, chưa thay cho hướng dẫn lắp đã thử thực tế.

## Cách đề cập khi yêu cầu sửa

- “Cho **núm cầm CT21** to hơn, giữ nguyên rãnh T.”
- “Tăng **độ dày cánh cửa CT02**, giữ vị trí lỗ trục CT08.”
- “Nới khe giữa **CT05 và CT03** ở bản lề trên.”
- “Đổi vị trí **chốt CT16 trên đĩa CT10**.”
- “Làm chữ/số trên **CT07** rõ hơn.”

Muốn mở riêng một chi tiết: mở `mini-vault.scad`, chọn **Display → part** bằng tên source nêu ở mục tương ứng. Muốn xem tương quan vị trí: chọn `assembly`; muốn bung cụm: chọn `exploded`. STL theo hướng in nằm trong [bộ 200](https://github.com/TimTini/mini-vault/releases/latest) và [bộ 220](https://github.com/TimTini/mini-vault/releases/latest); chúng dùng cùng tên selector nhưng khác preset/kích thước so với ảnh Default trong danh mục này.
