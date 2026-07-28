const { Component } = require('inferno');
const classname = require('hexo-component-inferno/lib/util/classname');
const Head = require('./common/head');
const Navbar = require('./common/navbar');
const Widgets = require('./common/widgets');
const Footer = require('./common/footer');
const Scripts = require('./common/scripts');
const Search = require('./common/search');

module.exports = class extends Component {
    render() {
        const { site, config, page, helper, body } = this.props;
        const { use_pjax } = config;
        const { __, my_cdn, url_for } = helper;

        var isMath = page.mathJax != undefined && page.mathJax;
        const language = page.lang || page.language || config.language;
        const columnCount = Widgets.getColumnCount(config.widgets);

        var mathJaxJs = `function loadMathJax() {
            $.getScript("//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML", function () {
                MathJax.Hub.Config({ tex2jax: { inlineMath: [['$', '$'], ['\\(', '\\)']] } });
                var math = document.getElementsByClassName("entry-content")[0];
                MathJax.Hub.Queue(["Typeset", MathJax.Hub, math]);
            });
        };loadMathJax();`;

        var pjaxJs = `var pjax = new Pjax({
            elements: "a",
            selectors: [".section", "title"],
            cache: true,
            cacheBust: false
        });
        document.addEventListener('pjax:complete', function () {
            $(".section").css({opacity:1});
            loadMainJs(jQuery, window.moment, window.ClipboardJS, window.RBLThemeSettings);
            loadBackTop();
            loadBusuanzi();
            if(typeof loadBanner == 'function'){ loadBanner(); }
        });`;

        let isPageOrPost = page.layout == 'page' || page.layout == 'post';
        return <html lang={language ? language.substr(0, 2) : ''}>
            <Head site={site} config={config} helper={helper} page={page} />
            <body className={`is-${columnCount}-column has-navbar-fixed-top`}>
                <Navbar config={config} helper={helper} page={page} />
                <script type="text/javascript" src={my_cdn(url_for('/js/theme-setting.js'))}></script>
                <section class="section">
                    <div class="container">
                        <div class="columns">
                            <div class={classname({
                                column: true,
                                'order-2': true,
                                'column-main': true,
                                'is-12': columnCount === 1,
                                'is-8-tablet is-8-desktop is-6-widescreen': (page.layout != 'post' && page.layout != 'page') && columnCount === 3,
                                'is-8-tablet is-8-desktop is-9-widescreen': columnCount === 2 || page.layout === 'post'
                            })} dangerouslySetInnerHTML={{__html: body}}></div>
                            <Widgets site={site} config={config} helper={helper} page={page} position={'left'}/>
                            {isPageOrPost ? null : <Widgets site={site} config={config} helper={helper} page={page} position={'right'}/>}
                        </div>
                    </div>
                </section>
                <Footer config={config} helper={helper} />
                <Scripts site={site} config={config} helper={helper} page={page} />
                <Search config={config} helper={helper} />
                {use_pjax ? <script src="https://cdn.jsdelivr.net/npm/pjax@0.2.8/pjax.js"></script> : null}
                {use_pjax ? <script type="text/javascript" dangerouslySetInnerHTML={{ __html: pjaxJs }}></script> : null}
                {isMath ? <script type="text/javascript" dangerouslySetInnerHTML={{ __html: mathJaxJs }}></script> : null}
            </body>
        </html>;
    }
};
