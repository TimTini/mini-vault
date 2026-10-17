# MINI-VAULT — đặt mã và lắp chốt

Mở `index.html` cùng `vendor/`, `mechanism.js`, `view.js`, `context-meshes.js` và `app.js`. Các tài nguyên đều local, dùng classic scripts. Đã kiểm tra giao diện bằng HTTP local; double-click `file://` chưa kiểm chứng trong phiên này.

## Sử dụng

**Tìm chốt và lượt quay** giữ nguyên mã nguyên1–16 và tra trực tiếp bảng tác giả. Lượt đầu4 để gom ba đĩa; các lượt tiếp theo được tính theo hành trình truyền động3→2→1 đĩa. Các ô lượt được cập nhật công khai; **Tìm theo lượt đã nhập** giữ lượt tự nhập và vẫn giữ nguyên bộ chốt theo bảng.

Mặc định **13/5/9** tương ứng **chốt5/2/3, lượt4/3/2** từ16. Ví dụ tác giả **13/9/2** tương ứng **chốt5/6/12, lượt4/2/2**. Cả hai mở bằng đúng mã nguyên trong mô hình hướng dẫn lý tưởng; giao diện không đề xuất số lẻ hiệu chỉnh. Người dùng đã xác nhận hướng dẫn tác giả hoạt động trên bộ đã lắp; đây là phản hồi thực tế của người dùng, không phải kiểm chứng vật lý độc lập của tool.

Nhìn núm từ bên ngoài: quay thuận chiều kim đồng hồ đến khi cả ba đĩa cùng quay rồi dừng ở số thứ nhất; đảo ngược đến khi đĩa2 và3 cùng quay rồi dừng ở số thứ hai; đảo thuận đến khi chỉ đĩa3 quay rồi dừng ở số thứ ba. Mỗi lần đảo chiều đếm lại từ1; vị trí đang đứng chưa tính là một lần gặp. Số lượt được hiển thị ứng với chuỗi bắt đầu tại16, không phải một bộ lượt dùng chung cho mọi mã. **Thử quay mã đã nhập** quay đúng các lượt đang hiển thị.

Không có lỗ cho số7 trên đĩa1, số2 trên đĩa2 và số5 trên đĩa3: tool báo rõ và giữ kết quả hợp lệ trước đó. Thử mã khi cửa còn mở trước khi đóng két.

1. Nhập ba số nguyên1–16 rồi chọn **Tìm chốt và lượt quay**. Tool dùng cơ cấu gốc scale1 và mặt nắp200 làm mốc minh họa.
2. Mặc định **Lắp từ mặt trong**: mặt có đầu lớn hướng về bạn, rãnh đĩa bên phải. Chọn hình **Đĩa 1 / 2 / 3** để xem riêng; lỗ cần đặt chốt tô vàng. Đĩa1 sát cửa, đĩa2 giữa, đĩa3 trong cùng. Các số quanh đĩa là số mã theo bảng tác giả; chỉ số SCAD0–14 ghi riêng trong tiêu đề.
3. Chọn **Cả nắp** để thấy toàn bộ mặt trong cửa, trục, vòng đỡ và vị trí cụm đĩa. Chọn một đĩa để trở lại hình gần. Lăn chuột để phóng to/thu nhỏ.
4. Chọn **Nhìn núm bên ngoài**: hình3D và sơ đồ lỗ cùng đổi phía nhìn, rãnh chuyển sang trái. Số lỗ và số đĩa gắn với chi tiết, chữ vẫn đọc xuôi.
5. **Thử quay mã đã nhập** tự chuyển sang phía núm ngoài và quay **⭮ → ⭯ → ⭮**, nghỉ1giây tại mỗi số. Mỗi chặng có thể gồm nhiều vòng. Chọn **Dừng** để ngừng. Khi rãnh khớp trong mô hình, chọn **Thử mở** để xem thanh gạt.

Đổi về hướng lắp đưa hình đĩa về tư thế mốc độc lập với chuyển động thử mã, giúp hình3D và sơ đồ lỗ luôn khớp. Góc mô phỏng được giữ riêng. Chế độ từng đĩa ẩn các đĩa khác để dễ quan sát; đây là cách hướng dẫn đặt chốt, chưa là mô phỏng thao tác tháo/lắp hay kiểm tra thứ tự khóa collar.

Phần **Cơ sở hướng dẫn và phạm vi mô phỏng** mô tả cách tra bảng và giới hạn animation.

## Mặt cửa và hướng chốt

Mặt cửa, trục và ba collar lấy từ STL hiện tại của từng bản200/220, giữ đúng tọa độ tương đối rồi đổi trục sang scene. Script [export-simulator-context.py](../work/export-simulator-context.py) tạo `context-meshes.js`, [report](../work/simulator-context-verification.json) lưu hash, bounds, số mặt, kiểm tra phép đổi trục và datum độc lập: mặt trong cửa tại sceneZ=3; mặt trước đĩa1 tạiZ=0; mặt tựa collar trùng mặt sau đĩa theo pitch5mm. Các tọa độ scene được chuẩn hóa theo size_scale để giữ hình dễ xem, source/STL giữ nguyên.

**Núm ngoài ← đầu nhỏ xanh | đĩa | đầu lớn vàng → trong thân.** Source SCAD tăngY về trong thân; scene tăngZ về núm ngoài. Đĩa1 sourceY−2..0; đầu nhỏY−4..0; đầu lớnY0..2. Scene tương ứng đĩaZ−2..0, đầu nhỏZ−2..2, đầu lớnZ−4..−2. [Kiểm tra6mesh hiện tại](../work/pin-orientation-verification.json), [script](../work/check-pin-orientation.py).

Đĩa/chốt/núm trong scene là hình giản lược phục vụ hướng dẫn; cửa/trục/collar là mesh thật. Hướng nhìn dùng `view.js`: khi nhìn mặt trong, đảo tọa độ ngang, giữ trục trên/dưới và số lỗ. Pose lắp giữ0° cho ba đĩa; pose thử mã dùng trạng thái động học.

## Kết quả và giới hạn

Luồng HTML dùng `authorGuide`→`authorHoles` và `Model(...,'author')`: tra bảng, tính lượt, minh họa truyền động lý tưởng. Lực truyền từ núm→đĩa3→đĩa2→đĩa1; thứ tự giữ mã1→2→3. Với lượt tự nhập, chốt không đổi; tool kiểm tra rãnh của các đĩa đã đặt qua cả ba chặng, không chỉ trạng thái cuối.

`solveCode`, `planCode` và biên tiếp xúc mesh giữ riêng cho kiểm tra chẩn đoán. Sai lệch khoảng2° và các điểm dừng số lẻ trước đây thuộc mô hình xấp xỉ này, không phải bằng chứng mã theo bảng tác giả sai trên bản in. Chúng không được dùng để chọn chốt hay trạng thái mở trong HTML.

Nguồn bảng: hình hướng dẫn tác giả do người dùng cung cấp, đối chiếu ví dụ13/9/2; trang gốc [MINI VAULT](https://makerworld.com/en/models/968614-mini-vault). Không coi việc mô phỏng khớp là đo lại toàn bộ cấu hình mesh.

Animation chưa tính ma sát/lực ép/biến dạng/độ nhám FDM. Trạng thái xanh và nút thử mở kiểm tra góc trong mô hình hướng dẫn; không thay thế thử lắp. Phân tích giao khối thực được lưu riêng trong report mesh.

## Kiểm chứng và tái tạo

Chạy tại thư mục project:

```powershell
node tests/test_assembly_view.cjs
node tests/test_assembly_ui.cjs
node tests/test_author_guide.cjs
node tests/test_auto_route.cjs
node tests/test_pickup_motion.cjs
node tests/test_inverse_code.cjs
node tests/test_dialing.cjs
node --check simulator/app.js
node --check simulator/view.js
python work/export-simulator-context.py
```

Test UI chạy handler thật và animation trong DOM fixture:13/5/9, ví dụ13/9/2,8/4/12, thử mở, lượt thủ công sai, lỗ không tồn tại, chọn đĩa/đổi phía/cả nắp. DOM fixture chưa là WebGL runtime. Các test inverse/dialing giữ mô hình mesh chẩn đoán và trace lịch sử riêng.

Các phiên trước đã quan sát chọn đĩa1/2/3, đổi mặt ngoài/trong và chế độCả nắp. Bản HTML theo bảng tác giả hiện được xác minh bằng Node/DOM fixture; chưa có kiểm tra WebGL trực tiếp. Lần thử browser trước bị chặn giao thức `file://`; không dùng cách khác để vượt policy. Không thaySCAD/preset/STL.

Three.js0.160.1 UMD, MIT tại `vendor/THREE-LICENSE.txt`. Nguồn: https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.min.js .
