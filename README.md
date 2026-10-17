# MINI-VAULT — OpenSCAD và hướng dẫn lắp chốt

Mô hình có tham số, bộ preset in FDM và tool HTML local để tìm vị trí chốt, xem mặt trong cửa và thử chuỗi quay **⭮ → ⭯ → ⭮**.

- [Danh mục 22 chi tiết có ảnh và mã CT](docs/CHI-TIET.md)
- [Tool đặt mã và hướng dẫn lắp](simulator/index.html)
- [Hướng dẫn tool và giới hạn kiểm chứng](simulator/README.md)
- [STL/3MF tải từ Releases](https://github.com/TimTini/mini-vault/releases/latest)
- [Phạm vi dữ liệu công khai](docs/PUBLICATION.md)

## Mở và sửa mô hình

Mở `mini-vault.scad` trong OpenSCAD, giữ `mini-vault.json`, `geometry/` và `profiles/` cạnh source. Đơn vị mm. Hình học dùng khối CSG liên tục và các biên dạng chức năng. Chọn `part="assembly"` để xem tư thế lắp hoặc chọn tên từng chi tiết để xuất riêng. `source_layout` giữ vị trí đo nguồn.

Miệng `housing` được dựng bằng các khối CSG có tên: khoang bo góc, đoạn loe, hốc khóa, chặn khóa và gờ bản lề. Dữ liệu 461 lát cắt cũ chỉ giữ để tham chiếu, không tham gia render vỏ. Xem [kích thước, quan hệ và cách kiểm chứng housing](docs/HOUSING-FEATURES.md).

Mặt sau `door` dùng các feature riêng: bệ trục, cửa lắp kiểu bayonet, càng/ray chốt, ngàm bản lề và chân gài nắp cơ cấu. Dữ liệu 475 lớp cũ chỉ giữ để tham chiếu. Xem [cấu trúc và cách kiểm chứng cửa](docs/DOOR-FEATURES.md).

Các preset:

- **Default:** vỏ142 ×100 ×84mm, `size_scale=1`.
- **150 - scale 1:** vỏ150 ×150 ×150mm, cơ cấu gốc.
- **200 - scale 1:** vỏ200 ×200 ×200mm, thành nguyên **3 mm**, tấm cửa **2,4 mm**, mặt lưng **2 mm**, cơ cấu gốc. Rãnh capsule được khoét trực tiếp **0,6 mm** vào bốn thành quanh miệng; đáy rãnh còn **2,4 mm**, phủ bì vẫn200 ×200 ×200mm. Vùng lắp cửa giữ kích thước cũ. Hiệu quả chịu lực và chống cong vênh cần thử in thực tế.
- **220 - scale 1.5:** vỏ220 ×220 ×220mm, cơ cấu phóng1,5lần và bù một số khe lắp.
- **220 - local reinforcement:** tỷ lệ1, gia cường cục bộ thành/gân và các mặt ghép liên quan.

`body_width/depth/height` là kích thước phủ bì của vỏ, kể cả khi bật rãnh. `housing_texture=0` là trơn, `1` là rãnh capsule; `housing_texture_depth/width/pitch` tính bằng mm cuối cùng. Độ sâu phải để lại ít nhất1,8mm thành sau khi khoét. Các kích thước cơ cấu được dựng trước `size_scale`, còn các khe được chọn được bù bằng `fit_gap(mm)=mm/size_scale`. Miền tham số xét trước tỷ lệ, ví dụ chiều rộng tối thiểu142×size_scale. Default giữ thông số gốc.

Kiểm chứng cửa 200 dày 2,4 mm: trước khi xuất lại, lưu manifest của bộ cửa 2 mm và ba STL theo trục source (`door`, `shaft`, `dial`) trong một thư mục backup. Dựng bộ 200 bằng exporter bên dưới, chạy `<python-PyChrono> work/chrono-housing-check.py poses`, rồi `<python-project> work/verify-door-thickness.py --backup <thu-muc-backup>`. Script đối chiếu 19 chi tiết không đổi, 231 cặp tĩnh, độ dày tấm cửa, khe trục/núm số và các đường chuyển động. Hai script kiểm tra tăng thành trước đó (`verify-thick-housing.py` và mode `inspect` của `chrono-housing-check.py`) dành riêng cho checkpoint cửa còn 2 mm; không dùng report cũ để xác nhận preset hiện tại.

PyChrono 10.0.0 dùng runtime riêng, không thuộc `requirements.txt`. Chrono giải ràng buộc motor bản lề tại [20,-0.5,0] mm và thanh trượt theo X; 361 tư thế cửa (bước 0,25°) và 121 vị trí trượt được đối chiếu giao khối bằng STL thật; đĩa/trục được kiểm tra thêm mỗi 2°. Đây là động học cưỡng bức, không phải mô phỏng lực tiếp xúc/ma sát PETG hoặc chứng nhận không kẹt. Xem [Chrono 10.0.0 motors](https://api.projectchrono.org/10.0.0/motors.html). Mức giảm cong vênh và độ vừa sau in cần kiểm chứng thực tế.

Với cửa dày hơn 2 mm, mép của lớp ngoài được lùi vào và vát để không tăng cọ khung khi mở; phần tấm 2 mm phía trong và các mặt lắp được giữ. Khi chuyển bộ 200 từ cửa 2 lên 2,4 mm, cần dùng `door` và `shaft` mới; `dial` chỉ dịch vị trí lắp, hình dạng chi tiết rời giữ nguyên. Bộ xuất hiện tại đã chứa đủ các chi tiết tương ứng.

Vạch chỉ số mặt ngoài cửa giữ kích thước cục bộ1×4mm rồi nhân tỷ lệ; bản200 là1×4mm, bản220/1.5 là1,5×6mm. Latch mở rộng theo bề rộng cửa và có đế đỡ sau cổ núm ở các bản lớn.

## Xem tư thế PyChrono

Viewer local phát lại đúng **361 tư thế cửa** (0–90°) và **121 vị trí chốt trượt** (0 đến −8 mm theo X) của preset **200 - scale 1**. Cần runtime PyChrono có Irrlicht và Tkinter, cùng bộ mesh/manifest và `work/thick-housing/chrono-poses.json` đã tạo tại máy; các dữ liệu local này không có trong source clone.

Mở từ PowerShell trên máy hiện tại:

```powershell
& 'python' 'work/chrono-viewer.py'
```

Hai cửa sổ xuất hiện: hình 3D và bảng điều khiển tiếng Việt. Chọn **Cửa** hoặc **Chốt trượt**, bấm **Phát/Dừng**, kéo thanh chọn tư thế hoặc bấm **±1 tư thế**. Kéo thanh sẽ dừng phát; mỗi lượt phát dài 6 giây. Trong cửa sổ 3D, giữ chuột trái và kéo để xoay, lăn bánh xe để zoom. Chế độ chốt chuyển camera sang mặt trong và tự ẩn vỏ; có thể bật lại vỏ bằng checkbox. Đóng một trong hai cửa sổ để thoát.

Viewer kiểm tra hash source, preset, script sinh pose và 22 mesh trước khi mở. Nếu dữ liệu đã cũ hoặc thiếu, viewer báo lỗi và dừng; không tự render lại hoặc ghi đè bằng chứng. Tái tạo input theo quy trình xuất/kiểm chứng phía trên trước khi mở lại. Chỉ kiểm tra dữ liệu mà không mở GUI:

```powershell
& 'python' 'work/chrono-viewer.py' --check
```

Kiểm chứng viewer gồm test stdlib và smoke GUI hữu hạn (mở rồi tự đóng, ghi ảnh/report vào `work/chrono-viewer-smoke/`):

```powershell
Set-Location '.'
& 'python' -m unittest discover -s tests -p test_chrono_viewer.py -v
& 'python' work/verify-chrono-viewer.py
```

Đây là phát lại động học đã lưu; viewer không chạy mô phỏng lực tiếp xúc, không đánh dấu vùng cấn và không xác nhận độ vừa sau in.

## File để in

Release gồm hai STL bố trí **22 chi tiết rời** cho200/1 và220/1.5, cùng ZIP chi tiết riêng. Trong slicer, dùng **Split to objects → Arrange** để chia ra nhiều bàn. Layout tổng lớn hơn một bàn; mỗi chi tiết đã được đặt mặt in và minZ=0, giữ kích thước bằng phép xoay/tịnh tiến cứng.

File `mini-vault-200-scale-1-dial-black-white.3mf` có hai part: thân đen và số/vạch trắng. Gán filament theo hai part trong slicer; file là mô hình, không phải lệnh gửi máy in.

Tám vạch ở vị trí không có số trên `dial` chạy từ bán kính 9 đến 18,5 mm,
ngang hàng số, rộng 1 mm và nổi 0,2 mm. Các vạch ngắn phía dưới số giữ nguyên.
Xuất lại bản hai màu sau khi xuất bộ STL 200 bằng `python work/export-colored-dial.py`;
kiểm tra file bằng `python -m unittest tests.test_colored_dial -v`.

Kiểm chứng trước đây gồm22/22chi tiết200 sliceoffline với profileA1/PLA/0,4mm/0,2mm, supporttắt; latch220 đã slice riêng. Toàn bộ bộ220 chưa slice cùng lượt. Việc này không thay thế preview trên profile thực tế và thử in/lắp.

Cơ cấu còn các giới hạn đã ghi nhận: tiếp xúc nhỏ tại hai góc cửa gần23° mở, retainingring trong hình assembly lệch rãnh0,75mm ởscale1.5, một số khe lắp sát, và khe dọc trục danh nghĩa đĩa/collar0mm. Lực, ma sát, độ nhám và độ bền vật lý chưa xác nhận. Các mẫu chuyển động/giao khối đã xét chỉ chứng minh trong phạm vi lấy mẫu.

## Tool đặt mã

Mở `simulator/index.html` cùng các file JS và `vendor/`. Tài nguyên đều local; có thể phục vụ bằng HTTP:

```powershell
python -m http.server 8000 --directory simulator
```

Mở `http://localhost:8000/`. Nhập pass mong muốn rồi chọn **Tìm chốt và lượt quay** để tự tìm lượt phù hợp, hoặc **Tìm theo lượt đã nhập** để giữ số lượt tự chọn. Bắt đầu ở16; mỗi lần đảo chiều đếm lại từ1. Tool xét3375bộ lỗ cho mỗi chuỗi lượt và giữ nguyên pass. Khi chưa khớp, kết quả ghi rõ phương án gần nhất.

Chế độ **Lắp từ mặt trong** đặt rãnh bên phải, đầu lớn của chốt hướng về người xem. Đĩa1 sát cửa, đĩa2 giữa, đĩa3 trong cùng; chọn từng đĩa hoặc **Cả nắp**. Đổi sang phía ngoài sẽ đổi cả hình3D và sơ đồ lỗ mà giữ nguyên index. **Thử quay mã đã nhập** quay đúng⭮⭯⭮ và số lượt đã chọn, không tự thêm vòng.

Tool hiện dùng cơ cấu gốc và mặt nắp200 làm mốc minh họa; bộ chọn200/220 đã bỏ. Mặt cửa/trục/collar lấy từ mesh hiện tại; đĩa/chốt/núm hiển thị giản lược. Kết quả thuộc mô hình tiếp xúc theo góc, chưa tính ma sát/biến dạng hoặc chứng nhận bản in mở đúng mã. Ví dụ8/4/12 với4/2/2còn lệch khoảng2,04°/1,40°/0,75° ởđĩa1/2/3.

Chọn **Tìm chốt và lượt quay** để tìm đồng thời chốt và lượt thay vì giữ mặc định4/2/2. Với13/5/9, tool chọn chốt5/2/3 và lượt4/3/2; mã nguyên còn lệch khoảng2°. Nút **Thử điểm dừng hiệu chỉnh** chạy riêng các số lẻ dự đoán, giữ nguyên mã nhập và ghi rõ đây là lượt hiệu chỉnh. Xem chi tiết trong [hướng dẫn simulator](simulator/README.md).

## Tái tạo và kiểm tra

Python dependencies nằm trong `requirements.txt`; dùng OpenSCAD có backendManifold. Cấu hình đường dẫn công cụ tại máy của bạn, qua `MINI_VAULT_OPENSCAD` hoặc tham số `--openscad`.

```powershell
python -m pip install -r requirements.txt
$env:MINI_VAULT_OPENSCAD = (Get-Command openscad).Source
python work/export-print-kit.py --preset '200 - scale 1' --openscad $env:MINI_VAULT_OPENSCAD
python work/verify-print-delivery.py --preset '200 - scale 1'
```

Exporter từ chối ghi đè STL đích đã tồn tại. File xuất, cache, log và metadata giữ local theo `.gitignore`. Muốn dùng rawSTLthamchiếu để đo lại, đặt input riêng ở `reference/MINI-VAULT.stl` và chạy `python analyze.py --check`; bản tham chiếu và lịch sử máy không nằm trong Git.

Kiểm tra logic simulator bằng Node.js:

```powershell
node tests/test_dial_visits.cjs
node tests/test_assembly_view.cjs
node tests/test_assembly_ui.cjs
node tests/test_inverse_code.cjs
node tests/test_dialing.cjs
node --check simulator/app.js
node --check simulator/mechanism.js
```

TestUI chạy handler thật trong DOMfixture, chưa phải WebGL. Các testCAD Python cần OpenSCAD, input/meshbaseline và evidence được tái tạo ởlocal; chúng không phải bộ kiểm tra độc lập chỉ với sourceclone. Source được công khai cùng các fixture số học cần cho testJS; backup/privateevidence không được đưa vào lịch sử Git.

## Nguồn mô hình

Tham khảo [MINI VAULT trên MakerWorld](https://makerworld.com/en/models/968614-mini-vault) và [video lắp của tác giả](https://www.youtube.com/watch?v=2BFG1QkyP0Q). Bản gốc và hình hướng dẫn thuộc tác giả tương ứng; repo không gán giấy phép mới cho các tài liệu đó. Thư việnThree.js giữ thông báoMIT tại `simulator/vendor/THREE-LICENSE.txt`.
