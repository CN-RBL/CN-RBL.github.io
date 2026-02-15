date = new Date();
year = date.getFullYear();
month = date.getMonth() + 1;
day = date.getDate();
if (year === 2026 && month === 2 && (day === 16 || day === 17)) {
    window.alert("新年快乐！")
    console.info("新年快乐！")
}

const pageWidth = document.documentElement.scrollWidth;
const pageHeight = document.documentElement.scrollHeight;
console.info(`页面宽度: ${pageWidth}px, 页面高度: ${pageHeight}px`);
