# MINI-VAULT — đặt mã và lắp chốt

Mở `index.html` cùng `vendor/`, `mechanism.js`, `view.js`, `context-meshes.js` và `app.js`. Các tài nguyên đều local, dùng classic scripts. Đã kiểm tra giao diện bằng HTTP local; double-click `file://` chưa kiểm chứng trong phiên này.

## Sử dụng

Lượt gặp số được nhập rõ cho từng chặng, mặc định **4 / 2 / 2**: bắt đầu kim ở16, quay⭮ đến8 lần thứ4, đảo⭯ đến4 lần thứ2, đảo⭮ đến12 lần thứ2. Mỗi lần đảo chiều đếm lại từ1; vị trí đang đứng chưa tính là một lần gặp. Đây là chuỗi đối chiếu, chưa xác nhận mở đúng8/4/12 trên bản in. Tool tìm chốt theo đúng các lượt bạn chọn, hiển thị góc quay từng chặng và số lần đã đi qua trong lúc chạy, giữ nguyên pass/lượt và không tự thêm360°. Sai lệch đĩa1/2/3 hiện dưới trạng thái mở.

Chuỗi8/4/12 với4/2/2 đi lần lượt1260°/630°/540°. Phương án gần nhất vẫn0/1/6, sai lệch cuối khoảng2,04°/1,40°/0,75°, chưa khớp. Con số43,05° của planner tự tăng chặng2 lên990° là kết quả lịch sử, không phải chuỗi hiện tại. Regression: `node tests/test_dial_visits.cjs`. APIlegacytự chọn vòng giữ cho bằng chứng/test lịch sử; UI hiện dùng routeexplicit.

1. Nhập mã mong muốn trên núm 1–16. Tool dùng cố định cơ cấu gốc scale1 và mặt nắp200; bộ chọn200/220 đã bỏ. Chọn **Tìm vị trí chốt**. Tool giữ nguyên pass và tìm trong 3.375 bộ lỗ; kết quả phân biệt khớp trong mô hình với phương án gần nhất.
2. Mặc định **Lắp từ mặt trong**: mặt có đầu lớn hướng về bạn, rãnh đĩa bên phải. Chọn hình **Đĩa 1 / 2 / 3** để xem riêng đúng chi tiết trên cửa; lỗ cần đặt chốt tô vàng. Đĩa1 sát cửa, đĩa2 giữa, đĩa3 trong cùng. Các số0–14 là chỉ số lỗ SCAD.
3. Chọn **Cả nắp** để thấy toàn bộ mặt trong cửa, trục, vòng đỡ và vị trí cụm đĩa. Chọn một đĩa để trở lại hình gần. Lăn chuột để phóng to/thu nhỏ.
4. Chọn **Nhìn núm bên ngoài**: hình3D và sơ đồ lỗ cùng đổi phía nhìn, rãnh chuyển sang trái. Số lỗ và số đĩa gắn với chi tiết, chữ vẫn đọc xuôi.
5. **Thử quay mã đã nhập** tự chuyển sang phía núm ngoài và quay **⭮ → ⭯ → ⭮**, nghỉ1giây tại mỗi số. Mỗi chặng có thể gồm nhiều vòng. Chọn **Dừng** để ngừng. Khi rãnh khớp trong mô hình, chọn **Thử mở** để xem thanh gạt.

Đổi về hướng lắp đưa hình đĩa về tư thế mốc độc lập với chuyển động thử mã, giúp hình3D và sơ đồ lỗ luôn khớp. Góc mô phỏng được giữ riêng. Chế độ từng đĩa ẩn các đĩa khác để dễ quan sát; đây là cách hướng dẫn đặt chốt, chưa là mô phỏng thao tác tháo/lắp hay kiểm tra thứ tự khóa collar.

Giao diện đã bỏ các nút xoay thủ công±vạch/±vòng, thanh kéo góc, điều chỉnh tốc độ, bung cơ cấu, nhìn xuyên, ẩn mặt số và chạy điểm dừng khác pass. Phần số liệu tiếp xúc nằm trong **Độ chính xác của phương án**.

## Mặt cửa và hướng chốt

Mặt cửa, trục và ba collar lấy từ STL hiện tại của từng bản200/220, giữ đúng tọa độ tương đối rồi đổi trục sang scene. Script [export-simulator-context.py](../work/export-simulator-context.py) tạo `context-meshes.js`, [report](../work/simulator-context-verification.json) lưu hash, bounds, số mặt, kiểm tra phép đổi trục và datum độc lập: mặt trong cửa tại sceneZ=3; mặt trước đĩa1 tạiZ=0; mặt tựa collar trùng mặt sau đĩa theo pitch5mm. Các tọa độ scene được chuẩn hóa theo size_scale để giữ hình dễ xem, source/STL giữ nguyên.

**Núm ngoài ← đầu nhỏ xanh | đĩa | đầu lớn vàng → trong thân.** Source SCAD tăngY về trong thân; scene tăngZ về núm ngoài. Đĩa1 sourceY−2..0; đầu nhỏY−4..0; đầu lớnY0..2. Scene tương ứng đĩaZ−2..0, đầu nhỏZ−2..2, đầu lớnZ−4..−2. [Kiểm tra6mesh hiện tại](../work/pin-orientation-verification.json), [script](../work/check-pin-orientation.py).

Đĩa/chốt/núm trong scene là hình giản lược phục vụ hướng dẫn; cửa/trục/collar là mesh thật. Hướng nhìn dùng `view.js`: khi nhìn mặt trong, đảo tọa độ ngang, giữ trục trên/dưới và số lỗ. Pose lắp giữ0° cho ba đĩa; pose thử mã dùng trạng thái động học.

## Kết quả và giới hạn

Bộ tìm kiếm xếp hạng sai số lớn nhất giữa ba điểm dừng tiếp xúc dự đoán và pass yêu cầu. Cấu hình chỉ được đánh dấu khớp khi sai số điểm dừng và sai lệch các đĩa đã đặt qua cả ba chặng đều dưới0,25°. Lực truyền từ núm→đĩa3→đĩa2→đĩa1; thứ tự giữ mã1→2→3.

Với **8–4–12**, bản200 hiện có phương án gần nhất **lỗ0/1/6**, điểm dừng dự đoán **7,909/4,058/11,967**; chưa có lời giải đáp ứng đúng pass trong mô hình hiện tại. Trang giữ cảnh báo này rõ ở đầu. [Bằng chứng tìm kiếm](../work/inverse-code-verification.json), [kiểm tra mesh](../docs/PUBLICATION.md).

Hai bộ lỗ200/scale1 `[0,1,6]`, `[8,4,12]` có biên tiếp xúc đo riêng; cấu hình gốc `[7,3,12]` có số đo200/1 và220/1.5. Các cấu hình khác tái sử dụng độ rộng tiếp xúc, được ghi là ước lượng. Xét3375 bộ lỗ trong mô hình chưa phải đo3375 bộ mesh. Bảng tác giả giữ làm tham khảo tại [author-instructions](https://makerworld.com/en/models/968614-mini-vault); runtime tìm ngược pass→bộ lỗ, thay cho tra bảng rồi coi là lời giải.

Mô hình chưa tính ma sát/lực ép/biến dạng/độ nhám FDM. Khe dọc trục danh nghĩa đĩa/collar hiện0mm; biên góc hằng còn xấp xỉ do lệch tâm núm/đĩa0,028609mm. Trạng thái xanh và nút thử mở kiểm tra góc trong mô hình, chưa chứng nhận bản in mở được. Phân tích giao khối thực được lưu riêng trong report mesh.

## Kiểm chứng và tái tạo

Chạy tại thư mục project:

```powershell
node tests/test_assembly_view.cjs
node tests/test_assembly_ui.cjs
node tests/test_inverse_code.cjs
node tests/test_dialing.cjs
node --check simulator/app.js
node --check simulator/view.js
python work/export-simulator-context.py
```

Test view kiểm tra phản chiếu lỗ/giữ chiều trên dưới, pose lắp trung tính, số đĩa và trạng thái mô phỏng. Test UI chạy handler thật trong DOM fixture: chọn đĩa, đổi phía, cả nắp,  thử mã đối chứng, validation. DOM fixture chưa là WebGL runtime. Test inverse/dialing giữ các ca âm8/4/12, khớp điểm dừng nhưng kéo lại đĩa, ánh xạ bảng và trace lịch sử.

Runtime đã quan sát chọn đĩa1/2/3 ở bản200, đổi mặt ngoài/trong cùng sơ đồ lỗ, chế độCả nắp và sửa DPIcanvas. Ca220 và animation trên giao diện mới chưa kiểm tra trực tiếp: công cụ browser bị tắt trong Work settings ở checkpoint cuối. Chúng đã có testDOM/logic và meshdatum; giữ giới hạn này riêng. Không thaySCAD/preset/STL.

Three.js0.160.1 UMD, MIT tại `vendor/THREE-LICENSE.txt`. Nguồn: https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.min.js .
