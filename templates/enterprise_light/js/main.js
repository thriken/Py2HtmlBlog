// ========== Header Scroll Effect ==========
const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// ========== Mobile Menu Toggle ==========
const menuToggle = document.querySelector('.menu-toggle');
const navMenu = document.querySelector('.nav-menu');

// Create overlay element
const navOverlay = document.createElement('div');
navOverlay.className = 'nav-overlay';
document.body.appendChild(navOverlay);

// Create close button inside nav menu
const navClose = document.createElement('button');
navClose.className = 'nav-close';
navClose.setAttribute('aria-label', '关闭菜单');
navClose.innerHTML = '<i class="fas fa-times"></i>';
if (navMenu) {
    navMenu.insertBefore(navClose, navMenu.firstChild);
}

function openMobileMenu() {
    menuToggle.classList.add('active');
    navMenu.classList.add('active');
    navOverlay.classList.add('active');
    document.body.classList.add('menu-open');
}

function closeMobileMenu() {
    menuToggle.classList.remove('active');
    navMenu.classList.remove('active');
    navOverlay.classList.remove('active');
    document.body.classList.remove('menu-open');
}

if (menuToggle) {
    menuToggle.addEventListener('click', () => {
        if (navMenu.classList.contains('active')) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    });

    // Close button click
    navClose.addEventListener('click', closeMobileMenu);

    // Overlay click to close
    navOverlay.addEventListener('click', closeMobileMenu);

    // Close menu when clicking a nav link
    navMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', closeMobileMenu);
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navMenu.classList.contains('active')) {
            closeMobileMenu();
        }
    });
}

// ========== Scroll Animation (IntersectionObserver) ==========
const animateElements = document.querySelectorAll('.animate-on-scroll');

if (animateElements.length > 0) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -40px 0px'
    });

    animateElements.forEach(el => observer.observe(el));
}

// ========== Number Counter Animation ==========
function animateCounter(el) {
    const target = el.textContent.trim();
    const hasPlus = target.includes('+');
    const hasPercent = target.includes('%');
    const numStr = target.replace(/[^0-9.]/g, '');
    const targetNum = parseFloat(numStr);
    const isDecimal = numStr.includes('.');
    const duration = 2000;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = eased * targetNum;

        let display;
        if (isDecimal) {
            display = current.toFixed(1);
        } else {
            display = Math.floor(current).toLocaleString('zh-CN');
        }

        if (hasPercent) display += '%';
        if (hasPlus) display += '+';

        el.textContent = display;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

const statNumbers = document.querySelectorAll('.stat-number');
if (statNumbers.length > 0) {
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(el => counterObserver.observe(el));
}

// ========== News Filter (news.html) ==========
const newsFilterTags = document.querySelectorAll('.news-filter .tag');
if (newsFilterTags.length > 0) {
    newsFilterTags.forEach(tag => {
        tag.addEventListener('click', () => {
            newsFilterTags.forEach(t => t.classList.remove('active'));
            tag.classList.add('active');
        });
    });
}

// ========== Cases Filter (cases.html) ==========
const caseFilterTags = document.querySelectorAll('section[style*="padding-bottom: 0"] .tag');
if (caseFilterTags.length > 0) {
    caseFilterTags.forEach(tag => {
        tag.addEventListener('click', () => {
            caseFilterTags.forEach(t => {
                t.style.background = '';
                t.style.color = '';
                t.style.borderColor = '';
            });
            tag.style.background = 'var(--gradient-1)';
            tag.style.color = '#fff';
            tag.style.borderColor = 'transparent';
        });
    });
}
// ========== FAQ Accordion Smooth Toggle ==========
const faqDetails = document.querySelectorAll('.faq-list details');
if (faqDetails.length > 0) {
    faqDetails.forEach(detail => {
        detail.addEventListener('toggle', () => {
            if (detail.open) {
                faqDetails.forEach(other => {
                    if (other !== detail && other.open) {
                        other.open = false;
                    }
                });
            }
        });
    });
}

// ========== Smooth Scroll for Anchor Links ==========
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
        const href = anchor.getAttribute('href');
        if (href === '#') return;
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// ========== Active Nav Link Highlight ==========
// 导航高亮由模板标签 {eyou:models currentstyle="active"} 处理
// 首页高亮由 header.htm 中的 {eyou:eq} 条件判断处理
// JS 不再干预，避免覆盖模板输出的 active class

// ========== Back to Top Button ==========
const backToTop = document.createElement('button');
backToTop.className = 'back-to-top';
backToTop.setAttribute('aria-label', '回到顶部');
backToTop.innerHTML = '<i class="fas fa-chevron-up"></i>';
document.body.appendChild(backToTop);

window.addEventListener('scroll', () => {
    if (window.scrollY > 400) {
        backToTop.classList.add('visible');
    } else {
        backToTop.classList.remove('visible');
    }
});

backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ========== Partner Scroll Drag ==========
const partnerWrapper = document.querySelector('.partner-scroll-wrapper');
if (partnerWrapper) {
    const track = partnerWrapper.querySelector('.partner-scroll-track');
    let isDragging = false;
    let startX = 0;
    let scrollLeft = 0;

    partnerWrapper.addEventListener('mousedown', (e) => {
        isDragging = true;
        partnerWrapper.classList.add('dragging');
        startX = e.pageX;
        const transform = getComputedStyle(track).transform;
        const matrix = new DOMMatrix(transform);
        scrollLeft = matrix.m41;
        track.style.animation = 'none';
        track.style.transform = 'translateX(' + scrollLeft + 'px)';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        e.preventDefault();
        const x = e.pageX;
        const walk = x - startX;
        track.style.transform = 'translateX(' + (scrollLeft + walk) + 'px)';
    });

    document.addEventListener('mouseup', () => {
        if (!isDragging) return;
        isDragging = false;
        partnerWrapper.classList.remove('dragging');
        const transform = getComputedStyle(track).transform;
        const matrix = new DOMMatrix(transform);
        const currentX = matrix.m41;
        const halfWidth = track.scrollWidth / 2;
        let normalizedX = currentX % halfWidth;
        if (normalizedX > 0) normalizedX -= halfWidth;
        track.style.transform = 'translateX(' + normalizedX + 'px)';
        const offset = -normalizedX;
        const totalWidth = halfWidth;
        const progress = offset / totalWidth;
        const duration = 30;
        const remaining = duration * (1 - progress);
        track.style.animation = 'none';
        track.offsetHeight;
        track.style.animation = 'partnerScroll ' + duration + 's linear infinite';
        track.style.animationDelay = '-' + (duration - remaining) + 's';
    });
}

// ========== Career Apply Modal ==========
const applyModal = document.getElementById('applyModal');
const applyModalClose = document.getElementById('applyModalClose');
const applyJobTitle = document.getElementById('applyJobTitle');
const applyForm = document.getElementById('applyForm');
const applyBtns = document.querySelectorAll('.apply-btn');

if (applyModal && applyBtns.length > 0) {
    applyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const jobName = btn.getAttribute('data-job');
            applyJobTitle.textContent = '申请职位：' + jobName;
            applyModal.classList.add('active');
            document.body.classList.add('menu-open');
        });
    });

    applyModalClose.addEventListener('click', () => {
        applyModal.classList.remove('active');
        document.body.classList.remove('menu-open');
    });

    applyModal.addEventListener('click', (e) => {
        if (e.target === applyModal) {
            applyModal.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && applyModal.classList.contains('active')) {
            applyModal.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    });

}
