# JOURNAL.md — nhật ký bàn giao (CHỈ ghi khi có việc DANG DỞ chưa xong hẳn)

> File này KHÔNG phải nơi ghi việc đã xong — việc xong ghi ở `docs/CHANGELOG.md`. AI KHÔNG thể "phát hiện" có bao nhiêu AI tool khác đang tham gia (mỗi CLI chạy phiên riêng biệt, không thấy phiên tool khác) — nên đừng chờ "biết chắc multi-agent" mới ghi. Dùng 2 trigger sau, áp dụng vô điều kiện:
> - **ĐỌC** — đầu MỌI phiên (bất kể tool nào, Claude Code/Codex/Gemini CLI), đọc file này trước khi bắt tay việc, giống thói quen đọc CHANGELOG.
> - **GHI** — cuối phiên, nếu task còn DANG DỞ nhiều bước (không phải lỗi vặt) mà phiên sắp/phải dừng, ghi lại: đang làm gì, xong tới đâu, còn thiếu gì. Ghi kể cả KHÔNG chắc ai sẽ tiếp theo — coi như ghi chú phòng hờ, vô hại nếu không ai đụng tiếp.
> Task đã xong hẳn, hoặc chỉ 1 AI làm trọn từ đầu tới cuối không gián đoạn → không có gì để ghi, để TRỐNG mục Log bên dưới.

## Quy ước ghi

- Entry mới thêm Ở TRÊN CÙNG mục Log (mới nhất trước). Không xoá entry cũ — chỉ thêm, TRỪ sửa tại chỗ dòng trạng thái của 1 task đang dở khi nó chuyển trạng thái (giống cập nhật checklist, không phải ghi log mới).
- Format tiêu đề: `### YYYY-MM-DD HH:MM — [Claude Code|Codex|Gemini CLI] — Tiêu đề ngắn`
- Status tag: 🟢 Decided · 🟡 Doing · 🔴 Blocked · ✅ Done-handoff (task dở đã bàn giao xong, sắp chuyển qua CHANGELOG) · ❓ Open question.
- Mỗi entry trả lời: đang làm gì / xong tới đâu / còn thiếu gì / AI tiếp theo cần biết gì để nối tiếp không phải dò lại từ đầu.
- Khi task DANG DỞ hoàn tất hẳn → xoá khỏi JOURNAL, chuyển thành 1 mục trong `docs/CHANGELOG.md` (JOURNAL không lưu lịch sử vĩnh viễn, chỉ lưu trạng thái đang treo).

---

## Log

(trống — chưa có bàn giao multi-agent nào)
