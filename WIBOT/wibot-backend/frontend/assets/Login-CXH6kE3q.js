import{j as e}from"./markdown-LDJaR8nE.js";import{r as m,N as u}from"./react-vendor-C8nPQJsR.js";import{L as b}from"./ui-vendor-DPgfHlC-.js";import{u as p}from"./useAuth-BP0GKK_3.js";import{u as g}from"./index-BPalpaHQ.js";import"./syntax-highlighter-BIivl8hH.js";const h={primary:"bg-accent hover:bg-accent-hover text-white",secondary:"bg-bg-secondary hover:bg-bg-user-msg text-text-primary border border-border",ghost:"bg-transparent hover:bg-bg-secondary text-text-primary",danger:"bg-red-600 hover:bg-red-700 text-white"},f={sm:"px-3 py-1.5 text-sm",md:"px-4 py-2 text-base",lg:"px-6 py-3 text-lg"};function y({variant:r="primary",size:o="md",onClick:s,children:i,disabled:a=!1,loading:t=!1,type:n="button",className:d=""}){const l=a||t;return e.jsxs("button",{type:n,onClick:s,disabled:l,className:`
        inline-flex items-center justify-center gap-2
        font-medium rounded-lg
        transition-colors duration-200
        focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-bg-primary
        disabled:opacity-50 disabled:cursor-not-allowed
        ${h[r]}
        ${f[o]}
        ${d}
      `,children:[t&&e.jsx(b,{className:"w-4 h-4 animate-spin"}),i]})}function x({type:r="text",value:o,onChange:s,placeholder:i,error:a,disabled:t=!1,className:n="",id:d,name:l}){return e.jsxs("div",{className:"w-full",children:[e.jsx("input",{type:r,id:d,name:l,value:o,onChange:s,placeholder:i,disabled:t,className:`
          w-full px-4 py-3
          bg-bg-secondary text-text-primary
          border rounded-lg
          placeholder:text-text-secondary
          transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed
          ${a?"border-red-500":"border-border"}
          ${n}
        `}),a&&e.jsx("p",{className:"mt-1 text-sm text-red-500",children:a})]})}function z(){const[r,o]=m.useState(""),[s,i]=m.useState(""),{login:a,isLoading:t,error:n}=p(),{isAuthenticated:d}=g();if(d)return e.jsx(u,{to:"/chat",replace:!0});const l=async c=>{c.preventDefault(),r.trim()&&s.trim()&&await a(r.trim(),s)};return e.jsxs("div",{className:"min-h-screen bg-bg-primary flex items-center justify-center p-4",children:[e.jsx("div",{className:"absolute inset-0 bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary"}),e.jsx("div",{className:"relative w-full max-w-md",children:e.jsxs("div",{className:"bg-bg-secondary border border-border rounded-2xl p-8 shadow-2xl",children:[e.jsxs("div",{className:"text-center mb-8",children:[e.jsx("h1",{className:"text-3xl font-bold text-text-primary mb-2",children:"WIBOT"}),e.jsx("p",{className:"text-text-secondary",children:"Connectez-vous pour continuer"})]}),e.jsxs("form",{onSubmit:l,className:"space-y-6",children:[e.jsxs("div",{children:[e.jsx("label",{htmlFor:"username",className:"block text-sm font-medium text-text-primary mb-2",children:"Nom d'utilisateur"}),e.jsx(x,{id:"username",name:"username",type:"text",value:r,onChange:c=>o(c.target.value),placeholder:"Entrez votre nom d'utilisateur",disabled:t})]}),e.jsxs("div",{children:[e.jsx("label",{htmlFor:"password",className:"block text-sm font-medium text-text-primary mb-2",children:"Mot de passe"}),e.jsx(x,{id:"password",name:"password",type:"password",value:s,onChange:c=>i(c.target.value),placeholder:"Entrez votre mot de passe",disabled:t})]}),n&&e.jsx("div",{className:"bg-red-500/10 border border-red-500/50 rounded-lg p-3",children:e.jsx("p",{className:"text-red-400 text-sm text-center",children:n})}),e.jsx(y,{type:"submit",variant:"primary",size:"lg",loading:t,disabled:!r.trim()||!s.trim(),className:"w-full",children:t?"Connexion...":"Se connecter"})]}),e.jsx("p",{className:"text-center text-text-secondary text-sm mt-8",children:"Chatbot interne WIDIP"})]})})]})}export{z as Login};
